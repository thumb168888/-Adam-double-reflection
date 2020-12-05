from selenium import webdriver
from PIL import Image
import time
import cv2
driver = webdriver.Chrome()
url="https://tw.stock.yahoo.com/future/charts.html?sid=WTX%26&sname=%E5%8F%B0%E6%8C%87%E6%9C%9F%E8%BF%91%E4%B8%80&mid=01&type=2"

driver.get(url)
driver.maximize_window()
print(driver.title)
def scroll():
	js="var q=document.documentElement.scrollTop=0"  
	driver.execute_script(js)  
	driver.execute_script("window.scrollTo(0, 200)") 
scroll()
Lx=570
Rx=Lx+780
Ly=250
Ry=Ly+430

Lx1=90
Rx1=Rx
Ly1=10
Ry1=Ry-330
while True:
	time.sleep(5)
	picname="yahoostock.png"
	driver.save_screenshot(picname)
	img = cv2.imread(picname)
	 # coordinate：[Ly:Ry , Lx:Rx]
	img2 = img[Ly:Ry , Lx:Rx]
	cv2.imwrite('yahoostock_output.png', img2)
	# cv2.imshow("screen box",img2)
	img2_reverse=cv2.flip(img2,-1)
	img2_reverse = img2_reverse[Ly1:Ry1 , Lx1:Rx1]
	img2_resized = cv2.resize(img2_reverse, (600,300), interpolation = cv2.INTER_AREA)
	cv2.imshow("reverse box",img2_resized )

	cv2.moveWindow("reverse box", 1000, 100)
	cv2.waitKey(1) #64bits! need a mask

cv2.destroyAllWindows()
driver.quit()
