## import nessary library

import cv2
import numpy as np
from contour_sort import *
from commonfunctions import *
from pathlib import Path
from detact_numbers_ocr import *
import xlwt
from detact_symbols import *
from detect_handwritten_digits import *
from detect_handwritten_ID import *

def kernal (img):
    
    (thresh, img_bin) = cv2.threshold(img, 128, 255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Invert the image
    img_bin = 255-img_bin
    # Defining a kernel length

    kernel_length = np.array(img).shape[1]//38
    
    # A verticle kernel of (1 X kernel_length), which will detect all the verticle lines from the image.
    verticle_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))

    # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
    hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))

    # A kernel of (3 X 3) ones.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    # Draw verticle lines
    verticle_lines_img = cv2.erode(img_bin, verticle_kernel, iterations=3)
    verticle_lines_img = cv2.dilate(verticle_lines_img, verticle_kernel, iterations=3)
    lines_ver = cv2.HoughLinesP(verticle_lines_img,1,np.pi/180,40,minLineLength=10,maxLineGap=20)

    for line  in lines_ver:
        for x1, y1, x2, y2 in line:
            verticle_lines_img=cv2.line(verticle_lines_img,(x1,0),(x2,verticle_lines_img.shape[0]),(255,255,255),1)
    cv2.imwrite('./kernal/verticle_lines_img.jpg',verticle_lines_img)
   
    # Draw horizontal lines
    horizontal_lines_img = cv2.erode(img_bin, hori_kernel, iterations=4)
    horizontal_lines_img = cv2.dilate(horizontal_lines_img, hori_kernel, iterations=3)
    lines_hor = cv2.HoughLinesP(horizontal_lines_img,2,np.pi/180,40,minLineLength=5,maxLineGap=10)
    for line  in lines_hor:
        for x1, y1, x2, y2 in line:

            horizontal_lines_img=cv2.line(horizontal_lines_img,(0,y1),(horizontal_lines_img.shape[1],y2),(255,255,255),1)
  
    cv2.imwrite('./kernal/horizontal_lines_img.jpg',horizontal_lines_img)

    # This function helps to add two image with specific weight parameter to get a third image as and of two image.
    img_final_bin=cv2.bitwise_and(verticle_lines_img, horizontal_lines_img)
    img_final_bin = cv2.erode(~img_final_bin, kernel, iterations=1)
    
    (thresh, img_output) = cv2.threshold(img_final_bin, 128,255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU) 
    
    cv2.imwrite('./kernal/img_final_threshold.jpg',img_output)

    return img_output

def cut_contours(img_final_bin,orignal_img,loaded_svc, loaded_knn, loaded_rf, loaded_lr,OCR_flag):
    contours = cv2.findContours(img_final_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    contours = sorted_counter(contours)
    rows=[]
    for c in range(len(contours)-1):
        x1, y1, w1, h1 = cv2.boundingRect(contours[c])
        x2, y2, w2, h2 = cv2.boundingRect(contours[c+1])
        if(x1==x2):
            rows.append(y1)
        else:
            rows.append(y1)
            break
    
    ## get nymber of rows and columns
    num_hor=len(rows)
    num_ver=len(contours)//num_hor
    wb = xlwt.Workbook()
    sheet = wb.add_sheet('Greed sheet',cell_overwrite_ok=True)
    badBG = xlwt.Pattern()
    badBG.pattern = badBG.SOLID_PATTERN
    badBG.pattern_fore_colour = 2
    badFontStyle = xlwt.XFStyle()
    badFontStyle.pattern = badBG
    ########### ID
    for col in range(0,1):
        sheet.write(0, col, "CODE")
        Path("contours/"+str(col)).mkdir(parents=True, exist_ok=True)
        for row in range(1,num_hor-1):
            # Returns the location and width,height for every contour
            x1, y1, w1, h1 = cv2.boundingRect(contours[row+num_hor*col])
            x2, y2, w2, h2 = cv2.boundingRect(contours[row+1+num_hor*col])
            x3, y3, w3, h3 = cv2.boundingRect(contours[row+num_hor*col+num_hor+1])
       
            ## crop image
            new_img = orignal_img[y1+h1:y3, x2+w2:x3]
            cv2.imwrite('./contours/'+str(col)+'/'+str(row)+'.jpg',new_img)
            ID=000
            if(OCR_flag):
                ID=detact_digit_ocr(row=row,col=col)
            else:
                ID=detect_id(row=row,col=col,loaded_svc=loaded_svc, loaded_knn=loaded_knn, loaded_rf=loaded_rf, loaded_lr=loaded_lr)
            sheet.write(row, col, ID)

    ########### digit
    for col in range(3,4):
        sheetCol=col-2
        sheet.write(0, sheetCol, sheetCol)
        
        Path("contours/"+str(sheetCol)).mkdir(parents=True, exist_ok=True)
        for row in range(1,num_hor-1):
            # Returns the location and width,height for every contour
            x1, y1, w1, h1 = cv2.boundingRect(contours[row+num_hor*col])
            x2, y2, w2, h2 = cv2.boundingRect(contours[row+1+num_hor*col])
            x3, y3, w3, h3 = cv2.boundingRect(contours[row+num_hor*col+num_hor+1])
            
            ## crop image
            new_img = orignal_img[y1+h1:y3, x2+w2:x3]
            cv2.imwrite('./contours/'+str(sheetCol)+'/'+str(row)+'.jpg',new_img)
            
            digit=0000
            if(OCR_flag):
                digit=detact_digit_ocr(row=row,col=sheetCol)
                if(len(digit)>0):
                    digit=digit[0]
            else:
                digit=detect_digit(row=row,col=sheetCol,loaded_svc=loaded_svc, loaded_knn=loaded_knn, loaded_rf=loaded_rf, loaded_lr=loaded_lr)
            sheet.write(row, sheetCol, digit)
            
           

    ########### symbols
    for col in range(4,num_ver-1):
        sheetCol=col-2
        sheet.write(0, sheetCol, sheetCol)
        Path("contours/"+str(sheetCol)).mkdir(parents=True, exist_ok=True)
        for row in range(1,num_hor-1):

            # Returns the location and width,height for every contour
            x1, y1, w1, h1 = cv2.boundingRect(contours[row+num_hor*col])
            x2, y2, w2, h2 = cv2.boundingRect(contours[row+1+num_hor*col])
            x3, y3, w3, h3 = cv2.boundingRect(contours[row+num_hor*col+num_hor+1])
           
            ## crop image
            new_img = orignal_img[y1+h1:y3, x2+w2:x3]
            cv2.imwrite('./contours/'+str(sheetCol)+'/'+str(row)+'.jpg',new_img)
            detact_symbols(sheet=sheet,row=row,col=sheetCol,badFontStyle=badFontStyle)

    wb.save('result Grades sheet.xls')



