import cv2
import numpy as np
import requests as r

class Captcha_solver:
    def __init__(self,fr_image_url,bg_image_url):
        self.bg_image_url = bg_image_url
        self.fr_image_url = fr_image_url
        self.bg_image_name = "bg_image.jpg"
        self.fr_image_name = "fr_image.jpg"
    def load_images(self):
        try:
            bg = r.get(self.bg_image_url)
            fr = r.get(self.fr_image_url)
            if bg.status_code == 200 and fr.status_code == 200:
                with open(self.bg_image_name,"wb") as file:
                    file.write(bg.content)
                    file.close()
                with open(self.fr_image_name,"wb") as file:
                    file.write(fr.content)
                    file.close()
                    return True
            else:
                return False
        except Exception as e:
            print(f"Error during loading captcha images: {e}")
            return False

    def prepare_images(self):
        self.bg_img = cv2.imread(self.bg_image_name)
        self.fr_img = cv2.imread(self.fr_image_name)

        fr_gray_img = cv2.cvtColor(self.fr_img, cv2.COLOR_BGR2GRAY)
        _, fr_threshold = cv2.threshold(fr_gray_img, 0, 255, cv2.THRESH_BINARY)
        fr_contours = cv2.findContours(fr_threshold,
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_NONE
                                    )
        fr_max_v = np.max(fr_contours[0][0],axis=0)
        fr_min_v = np.min(fr_contours[0][0],axis=0)

        fr_y_pos = [fr_min_v[0][1], fr_max_v[0][1]]
        fr_x_pos = [fr_min_v[0][0], fr_max_v[0][0]]
        #use
        self.fr_cropped_img = self.fr_img[fr_y_pos[0]:fr_y_pos[1], fr_x_pos[0]:fr_x_pos[1]]

        bg_cropped_img = self.bg_img[fr_y_pos[0]:fr_y_pos[1]]

        #use
        self.bg_cropped_img_gray = cv2.cvtColor(bg_cropped_img, cv2.COLOR_BGR2GRAY)


    def compare(self,add,alpha,fr_cropped_img,bg_cropped_img_gray):
        img_height, img_width = fr_cropped_img.shape[0], fr_cropped_img.shape[1]
        img_for_add = np.zeros((img_height,img_width, 3), dtype=np.uint8)+add

        with_added_image = cv2.addWeighted(fr_cropped_img,1-alpha,img_for_add,alpha,0)

        fr_mixed_img_gray = cv2.cvtColor(with_added_image, cv2.COLOR_BGR2GRAY)

        fr_cropped_img_gray = cv2.cvtColor(fr_cropped_img, cv2.COLOR_BGR2GRAY)

        max_val = 255*fr_mixed_img_gray.shape[1]*fr_mixed_img_gray.shape[0]
        result_data = []
        for x in range(0,bg_cropped_img_gray.shape[1]-img_width+1):
            #print(0+x,cuted_fr_img_gray.shape[1]+x,cuted_bg_img_gray.shape)
            bg_image_for_compare = bg_cropped_img_gray[:,x:img_width+x]
            bg_image_for_compare = np.where(fr_cropped_img_gray<=10,0,bg_image_for_compare)
            fr_mixed_img_gray = np.where(fr_cropped_img_gray<=10,0,fr_mixed_img_gray)
            sumofimage = np.sum(np.absolute(bg_image_for_compare-fr_mixed_img_gray))
            if sumofimage == 0:
                return [0,x]
            else:
                difference = sumofimage/max_val
                result_data.append([difference,x])
                def s(x):
                    return x[0]
                result_data.sort(reverse=False,key=s)
        return result_data[0]

    def solve_capthca(self):
        self.prepare_images()
        #white
        add = 255
        w_data = self.compare(add,0.25,self.fr_cropped_img,self.bg_cropped_img_gray)
        if (w_data[1]+60)<=320:
            if w_data[1]<3:
                minus = 0
            else:
                minus = 3
            #for image white cover
            img_white_cover = np.zeros((self.bg_img.shape[0],self.bg_img.shape[1], self.bg_img.shape[2]), dtype=np.uint8)+255
            w_alpha = 0.2
            #for manipulation
            w_add_image = np.zeros((self.bg_img.shape[0],self.bg_img.shape[1], self.bg_img.shape[2]), dtype=np.uint8)
            w_add_image[1:self.fr_img.shape[0]+1,w_data[1]-minus:w_data[1]+self.fr_img.shape[1]-minus] = self.fr_img

            #image with white cover on it
            image_with_white_cover = cv2.addWeighted(w_add_image,1-w_alpha,img_white_cover,w_alpha,0)
            image_with_white_cover = np.where(w_add_image>0,image_with_white_cover,self.bg_img)
            compare_white = np.sum(np.absolute(self.bg_img-image_with_white_cover))/(self.bg_img.shape[0]*self.bg_img.shape[1]*self.bg_img.shape[2]*255)
        else:
            compare_white = False

        #black
        add = 0
        b_data = self.compare(add,0.6,self.fr_cropped_img,self.bg_cropped_img_gray)
        if (b_data[1]+60)<=320:
            if b_data[1]<3:
                minus = 0
            else:
                minus = 3
            #for image white cover
            img_black_cover = np.zeros((self.bg_img.shape[0],self.bg_img.shape[1], self.bg_img.shape[2]), dtype=np.uint8)+0
            b_alpha = 0.5
            #for manipulation
            b_add_image = np.zeros((self.bg_img.shape[0],self.bg_img.shape[1], self.bg_img.shape[2]), dtype=np.uint8)
            b_add_image[1:self.fr_img.shape[0]+1,b_data[1]-minus:b_data[1]+self.fr_img.shape[1]-minus] = self.fr_img

            image_with_black_cover = cv2.addWeighted(b_add_image,1-b_alpha,img_black_cover,b_alpha,0)
            image_with_black_cover = np.where(image_with_black_cover>0,image_with_black_cover,self.bg_img)
            compare_black = np.sum(np.absolute(self.bg_img-image_with_black_cover))/(self.bg_img.shape[0]*self.bg_img.shape[1]*self.bg_img.shape[2]*255)
        else:
            compare_black = False

        #print(f"whited: {compare_white} blacked: {compare_black}")
        if compare_black != False and compare_white != False:
            if compare_black<compare_white:
                return b_data[1]
            else:
                return w_data[1]
        elif compare_black == False and compare_white == False:
            return False
        elif compare_black == False:
            return w_data[1]
        elif compare_white == False:
            return b_data[1]





if __name__ == "__main__":
    captcha_solver = Captcha_solver(
        "image_for_move",
        "background_img"
    )
    print(captcha_solver.solve_capthca())
