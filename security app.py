import cv2
import datetime as datetime
import pandas
import smtplib

# create table where we record when movement was present from start to finish
status_list = [None, None]
times = []
df = pandas.DataFrame(columns=["Start", "End"])

# declare what is out first frame is
first_frame = None
video = cv2.VideoCapture(0)

# format and name of the video
# we set FPS and resolution size of video
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out = cv2.VideoWriter('output.avi', fourcc, 24, (640, 480))

# start our recording loop
while video.isOpened():
    status = 0
    ret, frame = video.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21,), 0)

# using grayed out version of the original video because gray frame is more
# sensitive when dealing with motion recording and object recognition
# assigning initial frame from what we are going to compare rest of the frame
    if first_frame is None:
        first_frame = gray
        continue

# make our recordings from where we determine if movement happened or not
    delta_frame = cv2.absdiff(first_frame, gray)
    thrersh_frame = cv2.threshold(delta_frame, 30, 255, cv2.THRESH_BINARY)[1]
    thrersh_frame = cv2.dilate(thrersh_frame, None, iterations=2)
    (cnts,_) = cv2.findContours(thrersh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# add timestamp on the video
# .putText is responsible for formation of our time stamp
    font = cv2.FONT_HERSHEY_PLAIN
    text = str(datetime.datetime.now())
    cv2.putText(frame, text, (5, 25), font, 1, (0, 225, 225), 1)

# detects motion and writes into a file when motion is present
# status value is used to determine when the motion started or ended
# out.write records video only when motion is present
# the
    for contour in cnts:
        if cv2.contourArea(contour) < 700:
            status = 1
            out.write(frame)
    cv2.imshow('frame', frame)
    print(status)

# function to send up email notification when we detect motion
# we need to set up our email in order for this to work
# here URL where I have learned it https://youtu.be/Bg9r_yLk7VY?t=518
    def send_mail():
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login("your_email@gmail.com", "password")
        subject = 'movement was detected'
        body = 'check the stream'
        msg = f"SSubject: {subject}\n\n{body}"
        server.sendmail(
            "your_email@gmail.com",
            "recipient@gmail.com",
            msg
        )
        server.quit()

# method how we record when movement ocured
# we compare our status variable and see where it changes from 0 to 1 and 1 to 0
# we also send email when the motion is been detected
    status_list.append(status)
    if status_list[-1] == 1 and status_list[-2] == 0:
        times.append(datetime.datetime.now())
        send_mail()
    if status_list[-1] == 0 and status_list[-2] == 1:
        times.append(datetime.datetime.now())

# close our application and update our list where we write end and start of the movement
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        if status == 1:
            times.append(datetime.datetime.now())
        break

# we write timestamp when did the movement happened into CSV table
# we iterate through the list because the format of the list is
# list = [start time, end time, start time, end time]
for i in range(0, len(times), 2):
    df = df.append({"Start": times[i], "End": times[i+1]}, ignore_index=True)
df.to_csv("records of movement.csv")

# end everything when done with recording/showing image
video.release()
out.release()
cv2.destroyAllWindows()
