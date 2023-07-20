from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import pandas as pd
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import requests
import os
import time
from bs4 import BeautifulSoup
import utils
from selenium.webdriver.common.action_chains import ActionChains

#This code can scrape base.gov for contract information and download the Peças de Procedimento if they are stored in a zip file
#This code is WIP




#Search query url
url = "https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos&texto=&tipo=2&tipocontrato=5&cpv=&aqinfo=&adjudicante=&adjudicataria=&sel_price=price_c1&desdeprecocontrato=&ateprecocontrato=&desdeprecoefectivo=&ateprecoefectivo=&sel_date=date_c2&desdedatacontrato=&atedatacontrato=&desdedatapublicacao=2023-04-01&atedatapublicacao=2023-04-05&desdeprazoexecucao=&ateprazoexecucao=&desdedatafecho=&atedatafecho=&pais=187&distrito=0&concelho=0"
current_page = 0
#webdriver options
options = webdriver.ChromeOptions()
#options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-software-rasterizer')
options.add_argument("--clear-data")
options.add_argument("--disable-gpu")
executable_path = r"C:\Users\up201604212.CAMPUS\Downloads\chromedriver_win32\chromedriver.exe"
# Create a Service object
service = Service(executable_path)
driver = webdriver.Chrome(service=service, options=options)

# wait for the page title to contain the text "Base.gov.pt"
wait = WebDriverWait(driver, 40)


#get webpage
driver.get(url)
time.sleep(3)
# Loop through all the pages
while True:
    # Scrape the information from the current page
    # wait for the table to be present in the DOM
    time.sleep(5)
    #table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="no-more-tables-mx767"]'))) 
    table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@class="table table-striped"]')))
    # once the table is present, get its HTML content
    table_html = table.get_attribute('outerHTML')
    #find table 
    ##print("Table: ")
    soup = BeautifulSoup(table_html, 'html.parser')
    objeto_contrato = soup.find('td', {'data-title': 'Objeto do contrato'}).text.strip()
    ##print(objeto_contrato)
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
        time.sleep(5)
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
            print(link_value)
            #helpfull prints
            print("LINK VALUE")
            print(link_value)  # will output the link value
            if "vortal.biz" in link_value:
                utils.download_vortal(link_value=link_value, driver=driver, link_element=link_element, wait=wait)
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
                
            elif "anogov" in link_value:
                link_anogov = link_value.split("/")[-1]
                link_anogov = link_value.replace(link_anogov,"")
                print("-----É ANOGOV-----")
                print(link_anogov)
                link_value = os.path.basename(link_value).replace('/', '_').replace(':', '_').replace(" ","_").replace(".", "_").replace("=", "_").replace("?","_")
                if not os.path.exists(f'Filedump/{link_value}'):
                    os.makedirs(f'Filedump/{link_value}')
                link_element.click()
                wait.until(EC.number_of_windows_to_be(3))
                wait.until(EC.new_window_is_opened)
                time.sleep(3)
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3)
                anogov_table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="listaDocs:tabelaDocumentos"]')))
                tbody_anogov = anogov_table.find_element(By.TAG_NAME, "tbody")
                tbody_html = tbody_anogov.get_attribute("outerHTML") #for print porpuses
                num_rows = len(tbody_anogov.find_elements(By.TAG_NAME, "tr"))
                lista_html = []
                while True:
                    for i in range(num_rows + 3*num_rows-1):
                        try:
                            anogov_table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="listaDocs:tabelaDocumentos"]')))
                            tbody_anogov = anogov_table.find_element(By.TAG_NAME, "tbody")
                            rows_anogov = tbody_anogov.find_elements(By.TAG_NAME, "tr")
                            row_index = i 
                            num_rows = len(tbody_anogov.find_elements(By.TAG_NAME, "tr"))
                            if (i !=0):
                                row_index += 1
                                print(row_index)   
                            row_anogov = rows_anogov[row_index]
                            texto = row_anogov.get_attribute("outerHTML")
                            lista_html.append(texto)
                            #print("row: ", row_anogov)
                            #print("row html: ", texto)
                            wait2 = WebDriverWait(row_anogov, 3) 
                            time.sleep(2)
                            if row_anogov in rows_anogov:
                                try:
                                    hover_icon = wait2.until(EC.presence_of_element_located((By.CLASS_NAME, 'options-column')))
                                    # hover over the icon to make the button appear
                                    ActionChains(driver).move_to_element(hover_icon).perform()
                                    # wait for the button to be clickable
                                    button = wait2.until(EC.element_to_be_clickable((By.CLASS_NAME, 'options')))          
                                    button.click()
                                except:
                                    continue
                        except  IndexError:
                            continue        
                    for item in lista_html:
                        soup = BeautifulSoup(item, 'html.parser')
                        lista_de_requests = []
                        try:
                            link = soup.find('a', href=lambda href: href and 'downloadDiretoDocumento' in href)
                            sequence = link['href']
                            request_anogov = link_anogov + sequence
                            response_anogov = requests.get(request_anogov)
                            content_disposition_ano = response_anogov.headers.get('Content-Disposition')
                            print("ano", content_disposition_ano)
                            filename_anogov = content_disposition_ano.split("''")[1]
                            filename_anogov = filename_anogov.split(".")[0]
                            print("file", filename_anogov) 
                                                        
                            if ".pdf" in content_disposition_ano:
                                with open(f"Filedump/{link_value}/{filename_anogov}.pdf", "wb") as f:
                                    f.write(response_anogov.content)
                            elif ".xlsx" in content_disposition_ano:
                                with open(f"Filedump/{link_value}/{filename_anogov}.xlsx", "wb") as f:
                                    f.write(response_anogov.content)
                            elif ".xls" in content_disposition_ano:
                                with open(f"Filedump/{link_value}/{filename_anogov}.xls", "wb") as f:
                                    f.write(response_anogov.content)        
                            else:
                                with open(f"Filedump/{link_value}/{filename_anogov}.zip", "wb") as f:
                                    f.write(response_anogov.content)
                        except:
                            continue
                    
                    try:
                        next_page_anogov = driver.find_element(By.XPATH, '//*[@id="listaDocs:pag"]/tbody/tr/td[3]/div/input[3]')
                        next_page_anogov.click()
                        time.sleep(3)
                    except:
                        break
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()    
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
        
        driver.switch_to.window(driver.window_handles[-1])
        driver.close()
        
        driver.switch_to.window(driver.window_handles[0])

    # increment the page number and continue to the next page
    current_page += 1
    try:
        # Check if the "Next" button exists
        next_button = driver.find_element(By.XPATH, f'//*[@id="page_{current_page}"]')
        # Click the "Next" button
        next_button.click()
        time.sleep(20)  # wait for the page to load
    
    except:
        print("Last Page scraped")
        print("Scraping completed")
        print("Total number of scraped contracts: ", count)
        break

driver.quit()   
  
    
    
    
    
    
    
    #can use this to update PPPData in the future
    # find table body
    #ver_detalhe_tbody = ver_detalhe_table.find_element(By.TAG_NAME, "tbody")
    # and the rows
    #ver_detalhe_rows = ver_detalhe_tbody.find_elements(By.TAG_NAME, "tr")


    #falta testar erro do loop até aos 160 implementar função no base.py
    