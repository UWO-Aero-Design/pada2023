'''Akram Ayad
Jan 13 2024
learing how to use Optical Character recgition (OCR) useing this video
https://www.youtube.com/watch?v=6DjFscX4I_c&t=76s
'''
import cv2 
import pytesseract as tessORC
import numpy as np, cv2


#setting the tesact filepath is neccary to use the ocr and this code 
tessORC.pytesseract.tesseract_cmd= r'C:\\Program Files\\Tesseract-OCR\\tesseract'

# defining a function so it can be called if needed
def main():
    #reading the file a video 6min in legth will be posted to the teams chat in pada files 
    video = cv2.VideoCapture("Temp assets\\test_vid.mp4")
    #loop beuse its a video not a single image 
    while True:
        
        #gets the video  then gets hight and saves those vales 
        ret, image =video.read()
        
        #runs the Optical Character recegniton  for each frame  
        text= tessORC.image_to_data(image)

        # this loop will print the data retrived from runnning and sprated it then print it
        for x,i in enumerate(text.splitlines()):
            #first line of data is the name of each collum and braks the code beuse its a string so this by passes it 
            if x!=0:
                i=i.split()
                print(i)
                #if a word is located it saves poition informarion to then put a box aroud it and the text it sees 
                if len(i)==12:
                    x0,y0,x1,y1 =int(i[6]),int(i[7]),int(i[8]),int(i[9])
                    cv2.rectangle(image,(x0,y0),(x0+x1,y0+y1),(255,0,0),2)
                    cv2.putText(image,i[11],(x0,y0), cv2.FONT_HERSHEY_COMPLEX,1,(255,50,50),2)
        # to indicate when the text of a new frame is over 
        print("frame end")
                
        # loads the image with the text box on top 
        cv2.imshow('image window',image) 
        if cv2.waitKey(1) == ord('q'):
            break

    #ord returns the ascii value of key pressed q in this case if 0 it freaze
    cv2.destroyAllWindows#closes all windos 
main()