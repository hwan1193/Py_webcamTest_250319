# Py_webcamTest_250319
해당 프로젝트는 웹캠 코드에 동영상 녹화 기능을 가장 간단한 형태로 추가했습니다.

![image](https://github.com/user-attachments/assets/32fbc7d4-4108-484c-88c7-5a7fa69c1c42)


>실시간 웹캠 영상을 파일(예: .avi, .mp4)로 저장합니다.

>OpenCV의 VideoWriter를 사용할 수 있습니다.

>구현 방법 :

>UI: "Record" / "Stop Recording" 버튼 2개 추가

>Thread:

>self.video_writer = cv2.VideoWriter("output.avi", fourcc, fps, (width, height))

>각 프레임 읽을 때마다 self.video_writer.write(frame) 호출

>Stop 시 self.video_writer.release()
