#!/usr/bin/env python
# coding: utf-8

# In[1]:


#required installs (i.e. pip3 install in terminal): pandas, selenium, bs4, and possibly chromedriver(it may come with selenium)
#Download Chromedriver from: https://chromedriver.chromium.org/downloads
#To see what version to install: Go to chrome --> on top right click three dot icon --> help --> about Google Chrome
#Move the chrome driver to (/usr/local/bin) -- open finder -> Command+Shift+G -> search /usr/local/bin -> move from downloads

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import time
import os
from datetime import datetime
import pandas as pd
import re
import caffeine
import random
import schedule
import gender_guesser.detector as gender
d = gender.Detector()
import collections
import matplotlib.pyplot as plt
import openpyxl
from openpyxl import load_workbook
get_ipython().run_line_magic('matplotlib', 'inline')
caffeine.on(display=True)

page = input("Enter the Company Linkedin URL: ")
company_name = page[33:-1]

try:
    f= open("{}/{}_credentials.txt".format(company_name,company_name),"r")
    contents = f.read()
    username = contents.replace("=",",").split(",")[1]
    password = contents.replace("=",",").split(",")[3]
    user_index = int(contents.replace("=",",").split(",")[7])
    
except:
     if os.path.isdir(company_name) == False:
        try:
            os.mkdir(company_name)
        except OSError:
            print ("Creation of the directory %s failed" % company_name)
        else:
            print ("Successfully created the directory %s " % company_name)

        f= open("{}/{}_credentials.txt".format(company_name,company_name),"w+")
        username = input('Enter your linkedin username: ')
        password = input('Enter your linkedin password: ')
        user_index = 0
        f.write("username={}, password={}, page={}, user_index={}".format(username,password,page,user_index))
        f.close()


# In[2]:


#Get any existing scraped data
try:
    scraped = pd.read_csv("{}/{}_linkedin_backup.csv".format(company_name,company_name))
    liker_names = list(scraped["Id"])
    user_gender = list(scraped["Gender"])
    liker_locations = list(scraped["Location"])
    liker_headlines = list(scraped["Headline"])
    user_bios = list(scraped["Bio"])
    est_ages = list(scraped["Age"])
    influencers = list(scraped["Followed Influencers"])
    companies = list(scraped["Followed Companies"])
except:
    liker_names = []
    user_gender = []
    liker_locations = []
    liker_headlines = []
    user_bios = []
    est_ages = []
    influencers = []
    companies = []
    pass

#Get the Meta Data
try:
    linkedin_pages = pd.read_csv("meta_data.csv")
    interest_pages = list(linkedin_pages["Interest Pages"])
    follower_counts = list(linkedin_pages["Follower Counts"])
    follow_rate = list(linkedin_pages["Follow Rate"])
except:
    interest_pages = []
    follower_counts = []
    follow_rate = []


# In[3]:


#accessing Chromedriver
browser = webdriver.Chrome('chromedriver')

#Open login page
browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

#Enter login info:
elementID = browser.find_element_by_id('username')
elementID.send_keys(username)

elementID = browser.find_element_by_id('password')
elementID.send_keys(password)
elementID.submit()


# In[4]:


#Scrolls the main page
def scroll():
    #Simulate scrolling to capture all posts
    SCROLL_PAUSE_TIME = 1.5

    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# In[5]:


#Scrolls popups
def scroll_popup(class_name):
    #Simulate scrolling to capture all posts
    SCROLL_PAUSE_TIME = 1.5

    # Get scroll height
    js_code = "return document.getElementsByClassName('{}')[0].scrollHeight".format(class_name)
    last_height = browser.execute_script(js_code)

    while True:
        # Scroll down to bottom
        path = "//div[@class='{}']".format(class_name)
        browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", browser.find_element_by_xpath(path))

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script(js_code)
        if new_height == last_height:
            break
        last_height = new_height
        
        


# In[6]:


#Function that estimates user age based on earliest school date or earlier work date
def est_age():

    browser.switch_to.window(browser.window_handles[1])
    date = datetime.today()
    current_year = date.strftime("%Y")
    school_start_year = "9999"
    work_start_year = "9999"

    #Get page source
    user_profile = browser.page_source
    user_profile = bs(user_profile.encode("utf-8"), "html")


    #Look for earliest university start date
    try:
        grad_year = user_profile.findAll('p',{"class":"pv-entity__dates t-14 t-black--light t-normal"})
        
        if grad_year == []:
            browser.execute_script("window.scrollTo(0, 1000);")
            user_profile = browser.page_source
            user_profile = bs(user_profile.encode("utf-8"), "html")
            grad_year = user_profile.findAll('p',{"class":"pv-entity__dates t-14 t-black--light t-normal"})
            
        
        for d in grad_year:
            year = d.find('time').text.strip().replace(' ', '')
            start_year = re.sub(r'[a-zA-Z]', r'', year)
            start_year = start_year[0:4]
            if start_year < school_start_year:
                        school_start_year = start_year
    except:
        pass
    

    #Look for earlies work date
    try:
        #Click see more if it's there
        try:
            browser.find_element_by_xpath("//button[@class='pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link-without-visited-state']").click()
        except:
            time.sleep(1)
            pass

        work_start = user_profile.findAll('h4', {"class":"pv-entity__date-range t-14 t-black--light t-normal"})


        for d in work_start:
            start_date = d.find('span',class_=None)
            start_date = start_date.text.strip().replace(' ', '')
            start_date = re.sub(r'[a-zA-Z]', r'', start_date)
            start_year = start_date[0:4]
            if start_year < work_start_year:
                    work_start_year = start_year
    except:
        pass

    # Compare work and school start dates to avoid adult degress
    if school_start_year < work_start_year:
        #Estimate age based on avg university start age of 18
        est_birth_year = int(school_start_year) - 18
        est_age = int(current_year) - est_birth_year

    else:
        #Estimate age based on avg post college work start date of 22
        est_birth_year = int(work_start_year) - 22
        est_age = int(current_year) - est_birth_year

    if est_age <= 0:
        est_age = 'unknown'
    
    return est_age
        


# In[7]:


#Function that Scrapes user data
def get_user_data():
    
    global skip_count
      
    user_profile = browser.page_source
    user_profile = bs(user_profile.encode("utf-8"), "html")

    name = user_profile.find('li',{'class':"inline t-24 t-black t-normal break-words"})
    name = name.text.strip()

    #Make sure liker isn't a duplicate
    if name not in liker_names:

        skip_count = 0
        liker_names.append(name)
        split_name = name.split(" ", 2)
        #Get Liker Gender
        user_gender.append(d.get_gender(split_name[0])+"^ ")

        try:
            #Get Liker Location
            location = user_profile.find('li',{'class':"t-16 t-black t-normal inline-block"})
            liker_locations.append(location.text.strip()+"^ ")
        except:
            liker_locations.append("No Location")

        try:
            #Get Liker Headline
            headline = user_profile.find('h2',{"class":"mt1 t-18 t-black t-normal break-words"})
            liker_headlines.append(headline.text.strip())
        except:
            liker_headlines.append("No Headline")


        #Get Liker Bio
        try:
            browser.find_element_by_xpath("//a[@id='line-clamp-show-more-button']").click()
            time.sleep(1)
            user_profile = browser.page_source
            user_profile = bs(user_profile.encode("utf-8"), "html")
            bio = user_profile.findAll("span",{"class":"lt-line-clamp__raw-line"})
            user_bios.append(bio[0].text.strip())
        except:
            try:
                bio_lines = []
                bios = user_profile.findAll('span',{"class":"lt-line-clamp__line"})
                for b in bios:
                    bio_lines.append(b.text.strip())
                bio = ",".join(bio_lines).replace(",", ". ")
                user_bios.append(bio)

            except:
                user_bios.append('No Bio')
                pass

        #Get estimated age using our age function
        age = est_age()
        est_ages.append(age)



        #Click see more on user interests
        try: 
            interest_path = "//a[@data-control-name='view_interest_details']"
            browser.find_element_by_xpath(interest_path).click()
        except:
            scroll()
            time.sleep(1)
            try:
                interest_path = "//a[@data-control-name='view_interest_details']"
                browser.find_element_by_xpath(interest_path).click()
            except:
                influencers.append("No Influencers^ ")
                companies.append("No Companies^ ")
                return

        time.sleep(1)

        #Scrape the influencers the user follows
        try:
            influencer_path = "//a[@id='pv-interests-modal__following-influencers']"
            browser.find_element_by_xpath(influencer_path).click()

            #Scroll the end of list
            class_name = 'entity-all pv-interests-list ml4 pt2 ember-view'
            #interest_box_path = "//div[@class='entity-all pv-interests-list ml4 pt2 ember-view']"
            scroll_popup(class_name)

            influencer_page = browser.page_source
            influencer_page = bs(influencer_page.encode("utf-8"), "html")
            influencer_list = influencer_page.findAll("li",{"class":"entity-list-item"})


            user_influencers = ""
            for i in influencer_list:
                name = i.find("span",{"class":"pv-entity__summary-title-text"})
                name = name.text.strip()
                user_influencers += name + "^ "
                cleaned_name = name.replace(",","")
                
                if cleaned_name not in interest_pages:
                    interest_pages.append(cleaned_name)
                    follower_count = i.find('p', {"class":"pv-entity__follower-count"}).text.strip()
                    follower_count = follower_count.split(' ')
                    follower_count = follower_count[0]
                    follower_counts.append(follower_count)
                    
                    #Calc the follower rate
                    total_linkedin_users = 260000000
                    follow_percent = float(follower_count.replace(",",""))/total_linkedin_users * 100
                    follow_rate.append(follow_percent)

            influencers.append(user_influencers)


        except:
            influencers.append("No Influencers^ ")



        #Scrape the companies the user follows
        try:
            company_path = "//a[@id='pv-interests-modal__following-companies']"
            browser.find_element_by_xpath(company_path).click()

            time.sleep(2)

            #Scroll the end of list
            class_name = 'entity-all pv-interests-list ml4 pt2 ember-view'
            #interest_box_path = "//div[@class='entity-all pv-interests-list ml4 pt2 ember-view']"
            scroll_popup(class_name)


            company_page = browser.page_source
            company_page = bs(company_page.encode("utf-8"), "html")
            company_list = company_page.findAll("li",{"class":"entity-list-item"})


            user_companies = ""
            for i in company_list:
                name = i.find("span",{"class":"pv-entity__summary-title-text"})
                name = name.text.strip()
                user_companies += name + "^ "
                cleaned_name = name.replace(",","")
                
                if cleaned_name not in interest_pages:
                    interest_pages.append(cleaned_name)
                    follower_count = i.find('p', {"class":"pv-entity__follower-count"}).text.strip()
                    follower_count = follower_count.split(' ')
                    follower_count = follower_count[0]
                    follower_counts.append(follower_count)
                    
                    #Calc the follower rate
                    total_linkedin_users = 260000000
                    follow_percent = float(follower_count.replace(",",""))/total_linkedin_users * 100
                    follow_rate.append(follow_percent)

            companies.append(user_companies)
                

        except:
            companies.append("No Companies^ ")

    else:
        skip_count+=1
        time.sleep(random.randint(2,7))
        


# In[8]:


def word_counter(words):
    wordcount = {}
    for word in words.split('^ '):
        word = word.replace("\"","")
        word = word.replace("!","")
        word = word.replace("â€œ","")
        word = word.replace("â€˜","")
        word = word.replace("*","")
        word = word.replace("?","")
        word = word.replace("mostly_male","male")
        word = word.replace("mostly_female","female")
        
        exclude_words = ["No Influencers", "No Companies", "unknown", "andy", ""]
        
        if word not in exclude_words:
            if word not in wordcount:
                wordcount[word] = 1
            else:
                wordcount[word] += 1
        else:
            pass
            
    return wordcount


# In[9]:


def get_df(wc):
    
    total_scraped = len(user_gender)
    
    trimmed_count = collections.Counter(wc).most_common(300)

    words = []
    count = []
    percent = []
    interest_index = []
    interest_diff = []
    for item in trimmed_count:
        words.append(item[0])
        count.append(item[1])
        
    for c in count:
        percent.append(round(((c/total_scraped) * 100), 2))
    
    #make interest dictionary from meta data
    interest_dict = dict(zip(interest_pages, follow_rate))
            
    n=0
    for w in words:
        if w in list(interest_dict.keys()):
            if float(interest_dict[w]) != 0:
                index = float(percent[n])/float(interest_dict[w])
                interest_index.append(round(index,2))
                interest_diff.append(round(float(percent[n])-float(interest_dict[w]),2))
                n+=1
            else:
                interest_index.append("NA")
                interest_diff.append("NA")
                n+=1
        else:
            interest_index.append("NA")
            interest_diff.append("NA")
            n+=1
        

    data = {"Word": words,"Count": count, "Percentage": percent, "Index":interest_index, "Absolute Difference":interest_diff}

    df = pd.DataFrame(data, index =None)
    return df


# In[10]:


def clean_list(interest):
    clean_list = []
    for item in interest:
        clean = item.replace('^','')
        clean_list.append(clean.title())
    return clean_list


# In[11]:


def clean_interests(interest):
    clean_list = []
    for item in interest:
        clean = item.replace('^',',')
        clean_list.append(clean)
    return clean_list


# In[12]:


def count_interests():
    company_list = ",".join(companies).replace(',','')
    company_count = word_counter(company_list)
    common_companies = get_df(company_count)

    influencer_list = ",".join(influencers).replace(',','')
    influencer_count = word_counter(influencer_list)
    common_influencers = get_df(influencer_count)
    
    gender_list = ",".join(user_gender).replace(',','')
    gender_count = word_counter(gender_list)
    common_genders = get_df(gender_count)

    location_list = ",".join(liker_locations).replace(',','')
    location_count = word_counter(location_list)
    common_locations = get_df(location_count)
    
    return common_companies, common_influencers, common_genders, common_locations


# In[13]:


def plot_interests(df1,df2,df3,df4):
    company_plot = df1[0:24].plot.barh(x='Word',y='Percentage')
    company_plot.invert_yaxis()
    company_plot.set_ylabel('Companies')
    company_plot.figure.savefig("{}/c_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")

    influencer_plot = df2[0:24].plot.barh(x='Word',y='Percentage')
    influencer_plot.invert_yaxis()
    influencer_plot.set_ylabel('Influencers')
    influencer_plot.figure.savefig("{}/i_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")
    
    gender_plot = df3[0:24].plot.barh(x='Word',y='Percentage')
    gender_plot.invert_yaxis()
    gender_plot.set_ylabel('Gender')
    gender_plot.figure.savefig("{}/g_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")

    location_plot = df4[0:24].plot.barh(x='Word',y='Percentage')
    location_plot.invert_yaxis()
    location_plot.set_ylabel('Locations')
    location_plot.figure.savefig("{}/l_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")
    
    plt.close('all')


# In[14]:


def export_df():
    #Constructing Pandas Dataframe
    data = {
        "Gender": clean_list(user_gender),
        "Location": clean_list(liker_locations),
        "Age": est_ages,
        "Headline": liker_headlines,
        "Bio": user_bios,
        "Followed Influencers": clean_interests(influencers),
        "Followed Companies": clean_interests(companies)
    }

    df = pd.DataFrame(data)
    
    #Make backup data from to save our progress
    backup_data = {
        "Id": liker_names,
        "Gender": user_gender,
        "Location": liker_locations,
        "Age": est_ages,
        "Headline": liker_headlines,
        "Bio": user_bios,
        "Followed Influencers": influencers,
        "Followed Companies": companies    
    }
    
    backup_df = pd.DataFrame(backup_data)
    
    
    #Make a df of ages stats
    age_list = []
    for a in df["Age"]:
        if a != "unknown":
            age_list.append(int(a))
        else:
            pass
        
    age_data = {"Ages": age_list}    
    
    ages = pd.DataFrame(age_data)
    age_stats = ages.describe()
    age_stats = pd.DataFrame(age_stats)
    

    #Exporting csv to program folder for backup
    backup_df.to_csv("{}/{}_linkedin_backup.csv".format(company_name,company_name), encoding='utf-8', index=True)
    
    #Get data frames of interest counts
    common_companies, common_influencers, common_genders, common_locations = count_interests()
    
    #Plot the interest counts
    plot_interests(common_companies, common_influencers, common_genders, common_locations)
    
    time.sleep(1)
    
    #Create/Update Excel file
    writer = pd.ExcelWriter("{}/{}_linkedin.xlsx".format(company_name,company_name), engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Group Members', index=False)
    common_companies.to_excel(writer, sheet_name='Company Interest', index=False)
    common_influencers.to_excel(writer, sheet_name='Influencer Interest', index=False)
    age_stats.to_excel(writer, sheet_name='Demographic Stats', index=True)
    writer.save()
    
    wb = load_workbook("{}/{}_linkedin.xlsx".format(company_name,company_name))

    #Adding plots to the sheets
    cws = wb["Company Interest"]
    c_img = openpyxl.drawing.image.Image('{}/c_plot.png'.format(company_name))
    c_img.anchor = 'H5'
    cws.add_image(c_img)

    iws = wb["Influencer Interest"]
    i_img = openpyxl.drawing.image.Image('{}/i_plot.png'.format(company_name))
    i_img.anchor = 'H5'
    iws.add_image(i_img)
    
    dws = wb["Demographic Stats"]
    g_img = openpyxl.drawing.image.Image('{}/g_plot.png'.format(company_name))
    g_img.anchor = 'D2'
    dws.add_image(g_img)
    l_img = openpyxl.drawing.image.Image('{}/l_plot.png'.format(company_name))
    l_img.anchor = 'B21'
    dws.add_image(l_img)

    #Save Excel file
    wb.save("{}/{}_linkedin.xlsx".format(company_name,company_name))
    
    #Keep Track of where we are in the foller list
    f= open("{}/{}_credentials.txt".format(company_name,company_name),"w+")
    f.write("username={}, password={}, page={}, user_index={}".format(username,password,page,user_index))
    f.close()
        
    #Export the Meta Data
    meta_data = {
    "Interest Pages": interest_pages,
    "Follower Counts": follower_counts,
    "Follow Rate": follow_rate
    }

    meta_df = pd.DataFrame(meta_data)

    meta_df.to_csv("meta_data.csv", encoding='utf-8', index=True)


# In[15]:


def scrape_members(members):

    #Keeping track of number of page visits per day to stay under the limit
    daily_count = 0
    daily_limit = random.randint(2000,25000)
    
    global user_index

    #Loop through the members collecting data
    while user_index < len(members):
        try:
            ActionChains(browser).key_down(Keys.SHIFT).key_down(Keys.COMMAND).click(members[user_index]).key_up(Keys.SHIFT).key_up(Keys.COMMAND).perform()
            browser.switch_to.window(browser.window_handles[1])
            get_user_data()
            time.sleep(3)
            browser.close()
            time.sleep(2)
            browser.switch_to.window(browser.window_handles[0])
            failed_tries = 0
        except:
            failed_tries += 1

        #Iterate daily count & user_index
        user_index += 1
        daily_count+=1

        #Save progress if multiple of 10
        if user_index % 10 == 0:
            try:
                export_df()
                print("We have scraped {} users so far today. Saving our progress now.".format(str(daily_count)))
            except:
                print("Hmmm...Failed to Export.")


            #stop the program if we get more than 10 errors in row  
            if failed_tries > 10:
                print('There seems to be an error with the scraper')
                break


            #Random long sleep function to prevent linkedin rate limit
            time.sleep(random.randint(200,1200))

            #Stop if reached daily page view limit
            if daily_count >= daily_limit:
                print("Daily page limit of {} has been reached. Stopping for the day to prevent auto signout.".format(str(daily_limit)))
                while current_time() >= "01:00":
                    schedule.run_pending()
                    time.sleep(60)
                daily_count = 0

#             #Stop for the night
#             while current_time() < "07:05":
#                 schedule.run_pending()
#                 time.sleep(60)

        else:
            time.sleep(1)

        
        
  


# In[16]:


def current_time():
    current_time = datetime.now().strftime("%H:%M")
    return current_time


# In[17]:


def get_members():
    #scroll to end of list
    scroll()

    #find all group members
    members = browser.find_elements_by_xpath("//*[@class='ui-entity-action-row__link ember-view']")
    return members


# In[18]:


def main():
    #go to list of group members 
    browser.get(page + 'members/')
    members = get_members()
    time.sleep(5)
    scrape_members(members)
    print('scrape is complete')


# In[19]:


if __name__ == '__main__':
    main()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




