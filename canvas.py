# -*- coding: utf-8 -*-
"""
GUI for Canvas data mining program

"""
from tkinter import *
import requests
import os
from bs4 import BeautifulSoup as bs
#from OpenSSL.SSL import SysCallError
base_url = "https://canvas.tufts.edu/api/v1/courses/"
css_link = "https://drive.google.com/uc?export=download&id=17VN8-ECPGb3KtgI8JkCUAluo44-ZSt6o"
bg_link = "https://drive.google.com/uc?export=download&id=1qjwWCv5xYxyTJf2iqO8n0qJiQlkmAjF2"


"""
creates a dictionary of students and their user_ids from the canvas api
"""
def get_students(canvas_url, token):
    link = canvas_url
    if link[0:8] != "https://":
        print( "link invalid, try again with 'https://' before the link")
    token_text = "?access_token=%s" %token
    code = link.split("/")[-1]
    
    # try to send request
    while True:
        try:
            r = requests.get(base_url + code  + "/students" + token_text)
            break
        except requests.exceptions.RequestException:
            print("get students request failed, trying again..")
    
    students = {x["name"]:x["id"] for x in r.json()}
    return students

"""
creates a dictionary of assignment ids and their corresponding group ids
"""
def get_ass_and_groups(canvas_url, token):
    link = canvas_url
    if link[0:8] != "https://":
        return "link invalid, try again with 'https://' before the link"
    token_text = "?access_token=%s" %token
    code = link.split("/")[-1]
    param = "/discussion_topics"
    param1 = "/assignments"
    pages = "&per_page=60"
    
    while True:
        try:
            r = requests.get(base_url + code  + param + token_text + pages)
            break
        except requests.exceptions.RequestException:
            print("get assignments request failed, trying again")
    
    assign_codes = {x["id"]:x["assignment"]["assignment_group_id"] for x in r.json() if "assignment" in x}
    
    # get final assignment code
    while True:
        try:
            r = requests.get(base_url + code  + param1 + token_text + pages)
            break
        except requests.exceptions.RequestException:
            print("get assignments request failed, trying again")
    
    final = r.json()[-1]
    if "discussion_topic" not in final:
        final_code = final["id"]
    return (assign_codes, final_code)

"""
extracts all assignment submissions for the student and writes them in html format to a file 
stored in a folder of the same name. also downloads all media
name = student's name
student = student id 
assigns = dictionary of assignment codes and groups

"""
def readwork(name, student, assigns, canvas_url, token, final):
    link = canvas_url
    if link[0:8] != "https://":
        return "link invalid, try again with 'https://' before the link"
    token_text = "?access_token=%s" %token
    code = link.split("/")[-1]
    param = "/discussion_topics"
    param1 = "/view"
    param2 = "/assignment_groups"
    
    web_intro = "<html><head><title>Research data</title><link rel='stylesheet' href='files/style.css'/></head><body><div class='content'>"
     
    if not os.path.isdir("%s/files"%name):
        os.makedirs("%s/files"%name)

    fh = open(name + "/" + name + ".html", "w+")
    fh.write(web_intro)
    fh.close()
       
    #download stylesheet and background image
    while True:
            try:
                css = requests.get(css_link)
                bg = requests.get(bg_link)
                with open(name + "/files/style.css", "wb+") as f:
                    f.write(css.content)
                with open(name + "/files/bg.jpg", "wb+") as back:
                    back.write(bg.content)
                break
            except requests.exceptions.RequestException:
                print("download failed, trying again..")
    
    fh = open(name + "/" + name + ".html", "a+", encoding='utf-8')
    fh.write("<h1>%s</h1>"%name)
    
    for i in sorted(list(assigns.keys())):
        # get assignment title 
        while True:
            try:
                t = requests.get(base_url + code + param + "/" + str(i) + token_text)
                title = t.json()["title"]
                break
            except requests.exceptions.RequestException:
                print("get assignment title request failed, trying again..")
        
        #get assigment group title
        while True:
            try:
                q = requests.get(base_url + code + param2 + "/" +str(assigns[i]) + token_text)
                group = q.json()["name"]
                break
            except requests.exceptions.RequestException:
                print("get assignment Week request failed, trying again..")
                
        # get assignment submissions
        while True:
            try:
                r = requests.get(base_url + code + param + "/" + str(i) + param1 + token_text)
                break
            except requests.exceptions.RequestException:
                print("get assignment request failed, trying again..")
                
        if r.status_code // 100 != 2:
            break
        curr_att={}
        for ans in r.json()["view"]:

            if not "user_id" in ans:
                continue
            if ans['user_id'] == student:
                curr_msg = ans["message"]
                if "attachments" in ans:
                    curr_att = {x["display_name"]: x["url"] for x in ans["attachments"]}
                
                #write assignments to file
                fh.write("<h2>%s - %s</h2>%s" % (title, group, curr_msg) )
                fh.write("<h4>Attachments</h4>")
                for key in curr_att:
                    fh.write( "<p><a href='%s' class='attach'>%s</a></p>" %(curr_att[key], key) )
                break
        
    get_final(student, fh, final, code, token)   
    fh.write("</div></body></html>")
    fh.close()
    clean_up(name)
    
"""
this function adds the final project to the file for classes that have a final 
project as an assignment not a discussion
"""
def get_final(student, fh, final_code, code, token):
    
    if final_code == 0:
        return
    final_code = "/" + str(final_code)
    token_text = "?access_token=%s" %token
    param = "/assignments"
    param1 = "/submissions"
    pages = "&per_page=60"
    
    while True:
        try:
            r = requests.get(base_url + code  + param + final_code + param1 + token_text + pages)
            break
        except requests.exceptions.RequestException:
            print("get assignments request failed, trying again")
    for i in r.json():
        if i['user_id'] == student:
            fh.write("<h2>Final Project</h2>")
            if i["submission_type"] == "online_url":
                fh.write("<a href='%s'>Final Project here</a>"%i["url"])
            elif i["submission_type"] == "online_text_entry":
                fh.write(i["body"])
            elif i["submission_type"] == "online_upload":
                curr_att = {x["display_name"]: x["url"] for x in i["attachments"]}
                fh.write("<h4>Attachments</h4>")
                for key in curr_att:
                    fh.write( "<p><a href='%s' class='attach'>%s</a></p>" %(curr_att[key], key) )
            break
    

"""
    this function takes a html file and downloads all media files from it into 
    the current folder where the file is, then it converts all absolute urls to
    relative urls
"""
def clean_up(filename):
    fh = open(filename + "/" + filename + ".html", "r", encoding='utf-8')
    htm = bs(fh, "lxml")
    images = htm.find_all('img')
    for i in range(len(images)):
        print("downloading image %d"%i)
        try:
            link = images[i]['src']
        except KeyError:
            continue
        new_name = "files/image%d.jpg"%i
        
        while True:
            try:
                r = requests.get(link)
                with open(filename + "/" + new_name, "wb") as f:
                    f.write(r.content)
                images[i]['src'] = new_name
                break
            except requests.exceptions.RequestException:
                print("download failed, trying again..")
    
    vids = htm.find_all('video')
    for i in range(len(vids)):
        print("downloading video %d"%i)
        try:
            link = vids[i]['src']
        except KeyError:
            continue
        new_name = "files/file%d.mp4"%i
        
        while True:
            try:
                r = requests.get(link)
                with open(filename + "/" + new_name, "wb") as f:
                    f.write(r.content)
                vids[i]['src'] = new_name
                break
            except requests.exceptions.RequestException:
                print("download failed, trying again..")
        
    att = htm.find_all("a", "attach")
    for i in range(len(att)):
       print("downloading attachment %d"%i)
       try:
           link = att[i]['href']
       except KeyError:
           continue    
       new_name = "files/" + att[i].string
      
       while True:
            try:
               r = requests.get(link)
               with open(filename + "/" + new_name, "wb") as f:
                   f.write(r.content)
               att[i]['href'] = new_name
               break
            except requests.exceptions.RequestException:
                print("attachment download failed, trying again..")
        
    fh.close()
    fh = open(filename + "/" + filename + ".html", "w", encoding='utf-8')
    fh.write(htm.prettify())
    fh.close()

class App(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.place(height=500, width=500)
        self.config(width=500, height=500)
        self.create_widg()
    
    def create_widg(self):
        """create labels and text_boxes"""
        self.course_label = Label(self, text = "Paste course link  ")
        self.course_label.place(anchor=NW, relx=0.04, rely=0.02, relwidth=0.3, relheight=0.03)
        
        self.course_link = Entry(self)
        self.course_link.place(anchor=NW, relwidth=0.52, rely=0.02, relx=0.4, relheight=0.04 )
        
        self.auth_inst = Message(self, bd = 0, justify = "left",)
        self.auth_inst.place(anchor=NW, relx=0.08, rely=0.055, relheight=0.4)
        self.auth_inst["text"] = "Using this app requires authorization\nTo grant us access to your canvas classes;\n\n1. Go to your account settings page https://canvas.tufts.edu/profile/settings\n\n2. Scroll to Approved Integrations and click New Access token\n\n3. Fill the form and click Generate Token\n\n4. copy the token and paste below"
        
        self.auth_label = Label(self, text = "Paste authentication code")
        self.auth_label.place(anchor=NW, relx=0.08, rely=0.47, relwidth=0.35, relheight=0.03)
        
        self.auth_link = Entry(self)
        self.auth_link.place(anchor=NW, relwidth=0.48, rely=0.47, relx=0.44, relheight=0.04)
        
        self.submit = Button(self, text="Get Data", bg="black", fg="white")
        self.submit.place(anchor=NW, relwidth=0.3, relx=0.35, rely=0.52, relheight=0.05)
        self.submit["command"] = self.get_data
        
        self.log = Label(self, text="Logs:")
        self.log.place(anchor=NW, relx=0.08, rely=0.59, relheight=0.03)
        
        self.logbox = Text(self, bg="white", relief=GROOVE, cursor="arrow")
        self.logbox.place(anchor=NW, relx=0.08, rely=0.63, relwidth=0.84, relheight=0.36)
        self.logbox.insert( 0.0, "About to start\n" )
        self.logbox["state"] = DISABLED
        
    def get_data(self):
        self.logbox["state"] = NORMAL
        url = self.course_link.get()
        token = self.auth_link.get()
     
        print("Getting Students......\n")
        self.logbox.insert( END, "Getting Students......\n")
        student_list = get_students(url, token)
        
        print("Getting Assignment codes for each week....\n")
        self.logbox.insert( END, "Getting Assignments for each week....\n")
        ass_codes, final = get_ass_and_groups(url, token)
        
        for i in student_list:
            print("Getting Assignments for %s........\n" % i)
            self.logbox.insert( END, "Getting Assignments for %s\n" % i)
            readwork(i, student_list[i], ass_codes, url, token, final)
        
        print("*****\nDONE, you can delete the people you do not need\n*****")
        self.logbox.insert( END, "DONE, you can delete the people you do not need\n")
        self.logbox["state"] = DISABLED

def start_GUI():
    #start GUI window
    root = Tk()
    root.title("Extract Student Data")
    root.geometry("500x500")
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    start_GUI()
