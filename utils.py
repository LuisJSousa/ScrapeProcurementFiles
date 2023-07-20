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

def download_vortal(link_value, driver, link_element, wait):  
    print("É VORTAL!")
    link_value = os.path.basename(link_value).replace('/', '_').replace(':', '_').replace(" ","_").replace(".", "_").replace("=", "_").replace("?","_")
    if not os.path.exists(f'Filedump/{link_value}'):
        os.makedirs(f'Filedump/{link_value}')
    link_element.click()
    #wait for the new window to open
    wait.until(EC.number_of_windows_to_be(3))
    wait.until(EC.new_window_is_opened)
    time.sleep(5)
    #switch to the new window
    driver.switch_to.window(driver.window_handles[-1])
    print(len(driver.window_handles))
    # wait for the table to be present in the DOM
    vortal_table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grdGridDocumentList_tbl"]')))
    # find table body
    tbody_vortal = vortal_table.find_element(By.TAG_NAME, "tbody")
    # get all rows in table
    rows_vortal = tbody_vortal.find_elements(By.TAG_NAME, "tr")
    
    for x, row_vortal in enumerate(rows_vortal):
        try:
            last_column_element = row_vortal.find_element(By.XPATH, './/*[@id="grdGridDocumentListtd_thColumnDownloadDocument"]')
            last_column_contents = last_column_element.get_attribute("outerHTML")
            start_index = last_column_contents.find("documentFileId=") + len("documentFileId=")
            end_index = last_column_contents.find("&amp;", start_index)
            document_file_id = last_column_contents[start_index:end_index].strip().replace("' + '", "")
            print("document file", document_file_id)
            start_index2 = last_column_contents.find("&amp;mkey=") + len("&amp;mkey=")
            end_index2 = last_column_contents.find("'", start_index2)
            mkey = last_column_contents[start_index2:end_index2]
            print("mkey", mkey)
            file_vortal = f'https://community.vortal.biz/PRODPublic/Tendering/OpportunityDetail/DownloadFile?documentFileId={document_file_id}&mkey={mkey}'                       
            # create a requests.Session object to maintain cookies and headers
            session = requests.Session()
            # set headers and cookies
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.3",
                "Referer": "https://community.vortal.biz/",
            }
            cookies = {
                "PublicSessionCookie": "gnk1anpt4mbgyum3dkhdaqyk",
                "HAPRXSID": "10.101.2.33",
            }
            # make the initial request to get the redirect URL
            url = f"https://community.vortal.biz/PRODPublic/Tendering/OpportunityDetail/DownloadFile?documentFileId={document_file_id}&mkey={mkey}"
            print(url)
            response = session.get(url, headers=headers, cookies=cookies, timeout=30)
            if response.status_code == 200:
                redirect_url = response.url  # Get the final redirected URL
                print("redirect url", redirect_url)
                file_response = requests.get(redirect_url, headers=headers, cookies=cookies, timeout=30)
                print("file response")
                print(file_response)
                soup = BeautifulSoup(file_response.content, "html.parser")
                print("soup: ", soup)
                script_tag = soup.find("script")
                print("script tag: ", script_tag)
                if script_tag  is not None:
                    final_href = script_tag.text.strip().split("'")[1]
                    print("final href ", final_href)
                    # make the final request to download the file
                    final_url = f"https://community.vortal.biz{final_href}"
                    print("final url")
                    print(final_url)
                    final_response = session.get(final_url, headers=headers, cookies=cookies, timeout=30)
                    print("final response", final_response)
                    # save the file
                    content_disposition = final_response.headers.get('Content-Disposition')
                    filename_vortal = content_disposition.split('"')[1]
                    if ".pdf" in filename_vortal:
                        with open(f"Filedump/{link_value}/{filename_vortal}.pdf", "wb") as f:
                            f.write(final_response.content)
                    elif ".xlsx" in filename_vortal:
                        with open(f"Filedump/{link_value}/{filename_vortal}.xlsx", "wb") as f:
                            f.write(final_response.content)
                    elif ".xls" in filename_vortal:
                        with open(f"Filedump/{link_value}/{filename_vortal}.xls", "wb") as f:
                            f.write(final_response.content)        
                    else:
                        with open(f"Filedump/{link_value}/{filename_vortal}.zip", "wb") as f:
                            f.write(final_response.content)
                else:
                    print("No script tag found in the response.")
            else:
                print("Failed to access the initial URL.")
        except NoSuchElementException:
            print("Could not find last column element for row", x)
