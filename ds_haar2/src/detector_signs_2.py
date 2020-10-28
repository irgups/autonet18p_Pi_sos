#!/usr/bin/env python
# -*- coding: utf-8 -*- позволяет писать русские комментарии 
#можно уменьшить размер сжимания знака, например 64х64
#добавить выделение наибольшого контура
import rospy
import roslib
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from std_msgs.msg import String
import numpy as np
import cv2

global frame

#fourcc = cv2.VideoWriter_fourcc(*'XVID')
#out = cv2.VideoWriter('detector_traffic_signs.avi',fourcc, 25.0, (640,480))

detect = False	#переменная для выделения знаков
area = 3500	#пороговая площадь для обнаружения знаков

#пороги маски цвета
blue_color_low = (20,80,50) #blue_color_low = (50,1,100)	#blue_color_low = (74,1,123)	
blue_color_high = (255,255,255)	#blue_color_high = (255,255,255)
#пороги маски красного цвета
red_color_low = (0,100,40)	
red_color_high = (230,255, 255)

#путь к каскаду
#путь к каскадам
cas_f = '/home/ubuntu/catkin_ws/src/detector_signs/src/cascade/cascade_f_20x20.xml' 
cas_l = '/home/ubuntu/catkin_ws/src/detector_signs/src/cascade/cascade_left_20x20.xml' 
cas_r = '/home/ubuntu/catkin_ws/src/detector_signs/src/cascade//cascade_right_20x20.xml' 
cas_f_or_l = '/home/ubuntu/catkin_ws/src/detector_signs/src/cascade/cascade_f_or_l_20x20.xml' 
cas_f_or_r = '/home/ubuntu/catkin_ws/src/detector_signs/src/cascade/cascade_f_or_r_20x20.xml' 
cas_stop = '/home/ubuntu/catkin_ws/src/detector_signs/src/cascade/cascade_stop_20x20.xml' 
cas = '/home/ubuntu/catkin_ws/src/detector_signs/src/cascade/cascade_20x20.xml' 

cascade = cv2.CascadeClassifier(cas)
cascade_f = cv2.CascadeClassifier(cas_f)
cascade_l = cv2.CascadeClassifier(cas_l)
cascade_r = cv2.CascadeClassifier(cas_r)
cascade_f_or_l = cv2.CascadeClassifier(cas_f_or_l)
cascade_f_or_r = cv2.CascadeClassifier(cas_f_or_r)
cascade_stop = cv2.CascadeClassifier(cas_stop)

#путь к шаблонам
sample_f = '/home/ubuntu/catkin_ws/src/detector_signs/src/samples/forward.jpg'
sample_l = '/home/ubuntu/catkin_ws/src/detector_signs/src/samples/left.jpg'
sample_r = '/home/ubuntu/catkin_ws/src/detector_signs/src/samples/right.jpg'
sample_f_or_l = '/home/ubuntu/catkin_ws/src/detector_signs/src/samples/f_or_l.jpg'
sample_f_or_r = '/home/ubuntu/catkin_ws/src/detector_signs/src/samples/f_or_r.jpg'
sample_stop = '/home/ubuntu/catkin_ws/src/detector_signs/src/samples/stop.jpg'

samples_patch = [sample_f, sample_l, sample_r, sample_f_or_l, sample_f_or_r, sample_stop]
samples = {
1: 'forward',
2: 'left',
3: 'right',
4: 'f_or_l',
5: 'f_or_r',
6: 'stop'
}
#готовим шаблоны знаков
i_cas = 0
for value in samples.values():
	samples[value] = cv2.imread(samples_patch[i_cas])
	samples[value] = cv2.cvtColor(samples[value], cv2.COLOR_BGR2GRAY)
	samples[value] = cv2.resize(samples[value], (48,48))
	#cv2.imshow('sample', samples[value])
	#cv2.waitKey(0)
	i_cas+=1
#cv2.destroyAllWindows()

s = ['forward', 'left', 'right', 'f_or_l', 'f_or_r', 'stop']

key = 0

rospy.init_node('detector_node', anonymous=True)
pub_traffic_signs = rospy.Publisher('traffic_signs', String)

#порог обнаружения знака
def th(x):
    return {
        'forward': 1200,
        'left': 1100,
	'right': 1100,
	'f_or_l': 1100,
	'f_or_r': 1100,
	'stop': 1400,
    }[x]

def putDet(t):
	print t
	cv2.putText(frame, t, (x-5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
	cv2.rectangle(frame,(x,y),(x+w,y+h),(125,0,255),2) #выделяем обнаруженый знак
	pub_traffic_signs.publish(t)

def callback(data):
	global frame
	global key
	frame = CvBridge().imgmsg_to_cv2(data, "bgr8")	#захват кадра
	key = 1

def detector():
 while not rospy.is_shutdown():
	global frame
	global key
	global x
	global y
	global w
	global h
	if key == 1:	
		key = 0
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)	#делаем его ч/б
		equ = cv2.equalizeHist(gray)	#выравниваем гистограмму
		
		sign_cas = cascade.detectMultiScale(gray, 1.3, 1)	#применяем каскад
		
		for (x,y,w,h) in sign_cas:
			roi = frame[y:y+h, x:x+w]	#вырезаем детектированный объект
			height, width, channels = roi.shape	#получаем размеры детектированного объекта
			ar = height * width
			#print ar
			#если площадь детектированного объекта больше порогового, то рассматриваем дальше что это
			if ar >= area and ar <=area*4:
				#cv2.imshow('roi', roi)	#показываем вырезанный знак
			
				#преобразуем изображение в соответствуе с маской
				color_hls = cv2.cvtColor(roi, cv2.COLOR_BGR2HLS) #преобразование в цветовое пространство HLS
				#cv2.imshow('roi_hls', color_hls)	#показываем результат 
				only = cv2.inRange(color_hls, blue_color_low, blue_color_high)	#применяем цветовую маску
				#cv2.imshow('only_blue', only)	#показываем результат
		
				#подавляем шум
				mask = cv2.erode(only, None, iterations=1)
    				mask = cv2.dilate(mask, None, iterations=2)    
    	
    				#res_blue = cv2.bitwise_and(roi,roi, mask=mask) #накладываем маску цвета на бинарное изображение
				#cv2.imshow('mask', mask) #показывем результат преобразования по маске
	
				sign = cv2.resize(mask, (48,48))	#меняем размеры
				#cv2.imshow('sign', sign)	#показываем результат
		                #_frame = CvBridge().cv2_to_imgmsg(sign, "8UC3")
		                #pub_video.publish(_frame)
				
				detect = False
				
				#определяем какой знак
				for value in s:					
					count = 0
					#сравниваем с шаблоном
					for i in range(48):
						for j in range(48):
							if samples[value][i][j]==sign[i][j]:
								count+=1
				
					#print count, value	#выводим количество совпадений с конкретным шаблоном
					#уточнение детектированного знака
					if count > th(value):
						if value == 'forward':
							gray_2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
							sign_cas_f = cascade_f.detectMultiScale(gray_2, 1.3, 1)
							if sign_cas_f != ():
								detect = True
								putDet(value)
								
						elif value == 'left':
							gray_2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
							sign_cas_l = cascade_l.detectMultiScale(gray_2, 1.3, 1)
							if sign_cas_l != ():
								detect = True
								putDet(value)					
						elif value == 'right':
							gray_2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
							sign_cas_r = cascade_r.detectMultiScale(gray_2, 1.3, 1)
							if sign_cas_r != ():
								detect = True
								putDet(value)
						elif value == 'f_or_l':
							gray_2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
							sign_cas_f_or_l = cascade_f_or_l.detectMultiScale(gray_2, 1.3, 1)
							if sign_cas_f_or_l != ():
								detect = True
								putDet(value)
						elif value == 'f_or_r':
							gray_2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
							sign_cas_f_or_r = cascade_f_or_r.detectMultiScale(gray_2, 1.3, 1)
							if sign_cas_f_or_r != ():
								detect = True
								putDet(value)
						else:
							detect = False
							break
				
				#определяем не стоп ли это
				if detect == False:
					color_hls = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV) #преобразование в цветовое пространство HLS
					#cv2.imshow('roi_hls', color_hls)	#показываем результат
					only = cv2.inRange(color_hls, red_color_low, red_color_high)	#применяем цветовую маску
					#подавляем шум
					mask = cv2.erode(only, None, iterations=1)
    					mask = cv2.dilate(mask, None, iterations=2) 	
					sign = cv2.resize(mask, (48,48))	#меняем размеры
					#cv2.imshow('sign', sign)	#показываем результат

					count = 0
					#сравниваем с шаблоном
					for i in range(48):
						for j in range(48):
							if samples['stop'][i][j]==sign[i][j]:
								count+=1

					#print count, 'stop'	#выводим количество совпадений с конкретным шаблоном
					if count > th('stop'):
						gray_2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
						sign_cas_s = cascade_stop.detectMultiScale(gray_2, 1.3, 1)
						if sign_cas_s != ():
							putDet('stop')
							detect = True
						else:
							detect = False
							break

							
		#cv2.imshow('original', frame)
		#out.write(frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
		
		#_frame = CvBridge().cv2_to_imgmsg(frame, "bgr8")
       		#pub_video.publish(_frame)
		
		#rate.sleep()

if __name__ == '__main__':
	try:
		sub_video = rospy.Subscriber("video",Image, callback)
		detector()
	except rospy.ROSInterruptException:
		out.release()
		cap.release()
		pass

