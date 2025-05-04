
import pandas as pd
import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """Set up and return the Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
   
    
   
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def search_registration(driver, reg_number):
    """Search for a registration number, click on project name, then access project status"""
    try:
        
        search_box = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
        )
        search_box.clear()
        search_box.send_keys(reg_number)
        time.sleep(2)  
        
        
        project_name = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "table tr td:nth-child(3) a"))
        )
        print(f"Found project name: {project_name.text}")
        project_name.click()
        
        
        time.sleep(3)
        print(f"Project details page loaded: {driver.current_url}")
        
        
        print("Looking for project status link...")
        
        
        original_handles = driver.window_handles
        print(f"Window handles before clicking status button: {original_handles}")
        
        # Try different methods to find and click the status button
        try:
            # First attempt: Using CSS selector
            status_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-success"))
            )
            print(f"Found status button: {status_link.text}")
            status_link.click()
        except:
            try:
                
                status_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and contains(text(), 'Project Status')]"))
                )
                print(f"Found status button via XPATH: {status_link.text}")
                status_link.click()
            except:
                try:
                    # Third attempt: Using href attribute
                    status_link = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'project_status.php')]"))
                    )
                    print(f"Found status link via href: {status_link.get_attribute('href')}")
                    driver.execute_script("arguments[0].click();", status_link)
                except Exception as e:
                    print(f"All attempts to find status link failed: {str(e)}")
                    return False
        
       
        time.sleep(3)
        
       
        current_handles = driver.window_handles
        print(f"Window handles after clicking status button: {current_handles}")
        
        if len(current_handles) > len(original_handles):
           
            new_handle = [h for h in current_handles if h not in original_handles][0]
            driver.switch_to.window(new_handle)
            print(f"Switched to project status tab: {driver.current_url}")
        else:
            print("No new tab detected - status may have loaded in same tab")
        
        
        time.sleep(5)
        print("Project status page loaded and ready for data extraction")
        return True
        
    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error searching for registration {reg_number}: {str(e)}")
        return False

def extract_construction_status(driver, reg_number, output_file_path):
    """Extract the construction status table data and write immediately to CSV"""
    try:
        # Wait for page to fully load
        time.sleep(5)
        print("Page loaded, looking for construction status table...")
        
        # Find the table directly by ID
        try:
            status_table = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "agentDataTable"))
            )
            print("Found construction status table by ID")
        except:
            # Fallback to finding table near the construction status heading
            print("Could not find table by ID, trying to locate by heading...")
            try:
                status_heading = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//h3[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'STATUS OF CONSTRUCTION')]"))
                )
                status_table = status_heading.find_element(By.XPATH, "./following::table[1]")
                print("Found table using heading reference")
            except:
                # Last resort: try to find any table on the page
                print("Trying to find any table on the page...")
                tables = driver.find_elements(By.TAG_NAME, "table")
                if tables:
                    status_table = tables[0]  # Use the first table found
                    print(f"Found {len(tables)} tables, using the first one")
                else:
                    print("No tables found on the page")
                    
                    driver.save_screenshot(f"no_table_{reg_number.replace('/', '_')}.png")
                    return False
        
        
        rows = status_table.find_elements(By.TAG_NAME, "tr")
        print(f"Found {len(rows)} rows in the construction status table")
        
        if len(rows) <= 1:
            print("Warning: Table appears to have only a header row or is empty")
        
        
        header_row = rows[0]
        headers = header_row.find_elements(By.TAG_NAME, "th")
        if headers:
            header_texts = [h.text.strip() for h in headers]
            print(f"Table headers: {header_texts}")
            start_index = 1  
        else:
            
            print("No header row found, processing all rows")
            start_index = 0
        
        
        file_exists = os.path.isfile(output_file_path)
        
        with open(output_file_path, 'a', newline='', encoding='utf-8') as output_file:
            csv_writer = csv.writer(output_file, quoting=csv.QUOTE_MINIMAL)
            
           
            row_count = 0
            for row in rows[start_index:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells and len(cells) > 0:
                   
                    row_data = [reg_number]
                    
                   
                    for i, cell in enumerate(cells):
                        cell_text = cell.text.strip()
                        row_data.append(cell_text)
                    
                    
                    if len(row_data) > 1:  
                        csv_writer.writerow(row_data)
                        output_file.flush()  
                        row_count += 1
        
        print(f"Successfully extracted and wrote {row_count} rows of data for {reg_number}")
        return True
    except Exception as e:
        print(f"Error extracting construction status for {reg_number}: {str(e)}")
       
        try:
            screenshot_file = f"error_{reg_number.replace('/', '_')}.png"
            driver.save_screenshot(screenshot_file)
            print(f"Error screenshot saved to {screenshot_file}")
        except:
            print("Failed to save error screenshot")
        return False

def main():
    output_file_path = 'construction_status.csv'
    
   
    try:
        input_df = pd.read_csv('WB_input.csv')
        reg_numbers = input_df['registration_number'].tolist()  
        print(f"Loaded {len(reg_numbers)} registration numbers from input.csv")
    except Exception as e:
        print(f"Error reading input.csv: {str(e)}")
        reg_numbers = []
    
    if not reg_numbers:
        print("No registration numbers found in input.csv")
        return
    
    
    if not os.path.isfile(output_file_path):
        with open(output_file_path, 'a', newline='', encoding='utf-8') as output_file:
            csv_writer = csv.writer(output_file)
            
            csv_writer.writerow(['Registration Number', 'Building/Tower', 'Floor', 'Status', 'Completion Date'])
            print(f"Created output file: {output_file_path} with headers")
    
   
    driver = setup_driver()
    
   
    main_url = "https://rera.wb.gov.in/district_project.php?dcode=0"
    
    try:
       
        driver.get(main_url)
        print(f"Navigated to the initial page: {driver.current_url}")
        
        
        for i, reg_number in enumerate(reg_numbers):
            try:
                print(f"\n=======================================")
                print(f"Processing registration {i+1}/{len(reg_numbers)}: {reg_number}")
               
                
               
                print(f"Current window handles: {driver.window_handles}")
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                    print("Closed extra tab")
                
                driver.switch_to.window(driver.window_handles[0])
                print("Switched to main tab")
                
                
                if search_registration(driver, reg_number):
                   
                    extract_construction_status(driver, reg_number, output_file_path)
                else:
                    print(f"Failed to search for registration {reg_number}")
                    
                    with open('failed_registrations.txt', 'a') as fail_log:
                        fail_log.write(f"{reg_number}\n")
                        fail_log.flush()
                
                
                print("Cleaning up tabs...")
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                    print("Closed tab")
                
                driver.switch_to.window(driver.window_handles[0])
                print("Back to main window")
                
                
                driver.get(main_url)
                print(f"Returned to main search page: {driver.current_url}")
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing {reg_number}: {str(e)}")
                
                
                with open('failed_registrations.txt', 'a') as fail_log:
                    fail_log.write(f"{reg_number} - Error: {str(e)}\n")
                    fail_log.flush()
                
                
                try:
                    while len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                        driver.close()
                    
                    driver.switch_to.window(driver.window_handles[0])
                    # Return to main search page after error
                    driver.get(main_url)
                    print(f"Returned to main search page after error: {driver.current_url}")
                    time.sleep(2)
                except Exception as cleanup_error:
                    print(f"Error during tab cleanup: {str(cleanup_error)}")
    
    finally:
        driver.quit()
        print("Data extraction completed and saved to construction_status.csv")

if __name__ == "__main__":
    main()