from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import requests
import os
import time
from bs4 import BeautifulSoup
import utils

#This code can scrape base.gov for contract information and download the Peças de Procedimento if they are stored in a zip file
#This code is WIP

#Search query url
url = "https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos&texto=&tipo=2&tipocontrato=5&cpv=&aqinfo=&adjudicante=&adjudicataria=&sel_price=price_c1&desdeprecocontrato=&ateprecocontrato=&desdeprecoefectivo=&ateprecoefectivo=&sel_date=date_c4&desdedatacontrato=&atedatacontrato=&desdedatapublicacao=&atedatapublicacao=&desdeprazoexecucao=&ateprazoexecucao=&desdedatafecho=2023-02-22&atedatafecho=2023-02-22&pais=187&distrito=0&concelho=0"
current_page = 0
#webdriver options
options = webdriver.ChromeOptions()
#options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-software-rasterizer')
driver = webdriver.Chrome('chromedriver', options=options)

# wait for the page title to contain the text "Base.gov.pt"
wait = WebDriverWait(driver, 30)

#get webpage
driver.get(url)

# Loop through all the pages
while True:
    # Scrape the information from the current page
    # wait for the table to be present in the DOM
    table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@class="table table-striped"]')))

    # once the table is present, get its HTML content
    table_html = table.get_attribute('outerHTML')

    #find table 
    print("Table: ")
    soup = BeautifulSoup(table_html, 'html.parser')
    objeto_contrato = soup.find('td', {'data-title': 'Objeto do contrato'}).text.strip()
    print(objeto_contrato)

    # find table body
    tbody = table.find_element(By.TAG_NAME, "tbody")

    # get all rows in table
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    count = 0
    # loop through rows and get the "ver detalhe" URLs
    for i, row in enumerate(rows):
        while True:
            try:
                ver_detalhe = row.find_element(By.CSS_SELECTOR, "td[data-title='Ver detalhe'] a")
                count += 1
                #helpfull prints
                ver_detalhe_link = ver_detalhe.get_attribute('href') if ver_detalhe else None
                print("Ver detalher link: ", count)
                print(ver_detalhe_link)
                break
            except StaleElementReferenceException:
                continue

        #click the link to open a new window
        ver_detalhe.click()

        #wait for the new window to open
        wait.until(EC.number_of_windows_to_be(2))
        wait.until(EC.new_window_is_opened)

        #switch to the new window
        driver.switch_to.window(driver.window_handles[-1])
        
        # wait for the table to be present in the DOM
        ver_detalhe_table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="no-more-tables-mx767"]/table[1]')))

        # wait for the element to be clickable
        #wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="no-more-tables-mx767"]/table[1]/tbody/tr[23]/td/a')))
        
        # once the table is present, get its HTML content
        ver_detalhe_table_html = ver_detalhe_table.get_attribute('outerHTML')
        #helpfull prints
        #print("Ver detalhe: ")
        #print(ver_detalhe_table_html)

        # check if 'Filedump' folder exists, if not, create it
        if not os.path.exists('Filedump'):
            os.makedirs('Filedump')

        try:
            # find the element containing the 'Ligação para peças do procedimento' value
            link_element = driver.find_element(By.XPATH, '//*[@id="no-more-tables-mx767"]/table[1]/tbody/tr[23]/td/a')
            #wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="no-more-tables-mx767"]/table[1]/tbody/tr[23]/td/a')))
            # get the value of the 'Ligação para peças do procedimento' variable
            link_value = link_element.get_attribute('href')
            #helpfullprints
            print("LINK VALUE")
            print(link_value)  # will output the link value
            if "vortal.biz" in link_value:
                utils.download_vortal(link_value=link_value, driver=driver, link_element=link_element, wait=wait)
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
                print("AAAAAAAAAAAAAAAAAAAA")
                print(len(driver.window_handles))
            else:
                try:
                    # download file to 'Filedump' folder
                    filename = os.path.basename(link_value)
                    filename = os.path.basename(link_value).replace('/', '_').replace(':', '_').replace(" ","_")
                    response = requests.get(link_value, timeout=30) #set a timeout to 30 seconds if it takes to long to download the files in response
                    with open(f'Filedump/{filename}.zip', "wb") as f:
                        f.write(response.content)
                except requests.exceptions.Timeout:
                    print("Request timed out. Failed to download the file")
                except:
                    print("ESTE CONTRACTO NÃO TEM PEÇAS DO PROCEDIMENTO EM ZIP. Pode ser anagov")
            

        except NoSuchElementException:
            print("Link element not found")
        
            
        # close the current window and switch back to the original window
        print("AAAAAAAAAAAAAAAAAAAA")
        print(len(driver.window_handles))
        driver.switch_to.window(driver.window_handles[-1])
        driver.close()
        print("AAAAAAAAAAAAAAAAAAAA")
        print(len(driver.window_handles))
        driver.switch_to.window(driver.window_handles[0])

    # increment the page number and continue to the next page
    current_page += 1
    # Check if the "Next" button exists
    next_button = driver.find_element(By.XPATH, f'//*[@id="page_{current_page}"]')
    if not next_button.is_displayed():
        break

    # Click the "Next" button
    next_button.click()
    time.sleep(20)  # wait for the page to load

driver.quit()   
  
    
    
    
    
    
    
    #can use this to update PPPData in the future
    # find table body
    #ver_detalhe_tbody = ver_detalhe_table.find_element(By.TAG_NAME, "tbody")
    # and the rows
    #ver_detalhe_rows = ver_detalhe_tbody.find_elements(By.TAG_NAME, "tr")
    
    