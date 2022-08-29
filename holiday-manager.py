#imports needed for program to run
from datetime import datetime
from datetime import date
from datetime import timezone
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass, Field
import json 
from os.path import exists 
import config

#get config variables
from config import json_holidays_file
from config import save_to_file_location
from config import weather_api

#create needed variables
holiday_names = []
new_line = '\n'
week_range =[]
weather_week = {}
weather_week_list = []
weather_day = ''

#function to enhance readability
def make_space(str):
    print('='*len(str))

#create Data Classes

@dataclass
class Holiday:
    name: str
    date: date 

    def get_name(self):
        return self.name 

    def __str__(self):
        return self.name.title() + ' (' + self.date.strftime('%Y-%m-%d') + ')'

@dataclass
class HolidayList:
    inner_holidays : list 
    
    #add holiday in HolidayList inner_holidays 
    def user_input_holiday(self):
        print('\n Add a Holiday\n')
        make_space('Add a Holiday')
        global holiday_obj
        holiday_obj = ''

        holiday_name_input = input('\nHoliday Name: ').title()
        while True:
                holiday_date_tried_input = input('\nHoliday Date (format: yyyy-mm-dd): ')
                try:
                    holiday_date_input = datetime.strptime(holiday_date_tried_input, '%Y-%m-%d').date()
                    holiday_obj = Holiday(holiday_name_input, holiday_date_input)
                    break
                except ValueError:
                    print('Please enter data in correct format yyyy-mm-dd.')
                    continue
        return holiday_obj

    def add_holiday(self, holiday_obj):
        if isinstance(holiday_obj, Holiday) == True:
            if holiday_obj not in self.inner_holidays:
                self.inner_holidays.append(holiday_obj)
                print(f'{new_line}You have added the new holiday {holiday_obj.name} celebrated on {holiday_obj.date}!') 
            else:
                print(f'{holiday_obj.name} has already been entered. It cannot be added to the list again.')
        else:    
            print(f'{holiday_obj.name} is not from the Holiday class and cannot be added to the list.')
        print(f'{new_line}You have added to the list of Holidays. {new_line}{new_line}There are now {len(self.inner_holidays)} Holidays in the system list.')

    #find holiday in HolidayList inner_holidays
    def find_holiday(self, holiday_name, holiday_date):
        global holiday_found
        holiday_found = ''
        global holiday_to_find
        holiday_to_find = ''
        try:
            holiday_to_find = Holiday(holiday_name.title(), datetime.strptime(holiday_date, '%Y-%m-%d').date())
            if holiday_to_find in self.inner_holidays:
                holiday_found = True   
            else:
                print(f'Cannot find {holiday_name.title()} in holiday list.')
                holiday_found = False 
        except ValueError:
            print(f'Holiday date is not in the correct format: yyyy-mm-dd.Cannot find {holiday_name.title()} in holiday list.')
            holiday_found = False 

    #find & remove holiday in HolidayList inner_holidays
    def remove_holiday(self):
        print('\nRemove a Holiday\n')
        make_space('Remove a Holiday')
        holiday_name_input = input('\nName of Holiday to delete: ')
        holiday_date_input = input('Date of Holiday to delete (yyyy-mm-dd): ')
        self.find_holiday(holiday_name_input, holiday_date_input)
        if holiday_found == False:
            print(f'{new_line}Error:{new_line}{holiday_to_find} not found in holiday list.')
        else:
            print(f'{new_line}Success:{new_line}{holiday_to_find} has been removed from the holiday list.')
            self.inner_holidays.remove(holiday_to_find)

    #read in json and add holidays to inner list
    def read_json(self, file_location):
        f = open(file_location)
        data = json.load(f)['holidays']
        for item in data:
            name = item['name'].title()
            while True:
                date = item['date']
                try:
                    holiday_date_input = datetime.strptime(date, '%Y-%m-%d').date()
                    break
                except ValueError:
                    print(f'Unable to add {name} to holiday list due to improper formatting.')
                    break
            json_holiday_obj = Holiday(name, holiday_date_input)
            self.add_holiday(json_holiday_obj)

    #write out json to selected file
    def save_to_json(self, file_location):
        for holiday in self.inner_holidays:
            holiday.date = holiday.date.strftime('%Y-%m-%d')
        holiday_list_dics = [holiday.__dict__ for holiday in self.inner_holidays]
        json_str = json.dumps({'holidays': holiday_list_dics}, indent = 4)
        with open(file_location, 'w') as out:
            out.write(json_str)
        for holiday in self.inner_holidays:
            holiday.date = datetime.strptime(holiday.date, '%Y-%m-%d').date()

    def save_holiday_list(self):
        print('\nSaving Holiday List\n')
        make_space('Saving Holiday List')
        while True:
            save_choice = input('\nAre you sure you want to save your changes? [y/n]: ').lower()
            if save_choice == 'y':
                print('\nSuccess:\nYour changes have been saved.')
                self.save_to_json(save_to_file_location)
                break
            elif save_choice == 'n':
                print('\nCanceled:\nHoliday list file save canceled.')
                break
            else:
                print('Make a y or n selection please.')
                continue

    #scrape holidays from timeanddate.com (2 previous years, current year, 2 years into future)
    def scrape_holidays(self):
        date_hol = ''
        global name_list
        name_list = []
        global date_list
        date_list = []
        current_year = date.today().year
        for i in range(current_year - 2, current_year + 3):
            url = (f'https://www.timeanddate.com/holidays/us/{i}')
            html = requests.get(url).text 
            soup = BeautifulSoup(html, 'html.parser')
            tbody = soup.find('tbody')

            listy = tbody.find_all('a')
            for i in range(len(listy)):
                name = listy[i].text
                name_list.append(name)

            datey = tbody.find_all('tr')
            for i in range(len(datey)):
                if 'data-date' in datey[i].attrs:
                    date_input = int(datey[i].attrs['data-date'])/1000 + 86400
                    date_hol = datetime.fromtimestamp(date_input).date()
                    date_list.append(date_hol)    
               
        for i in range(len(name_list)):
            holiday_obj = Holiday(name_list[i], date_list[i])
            self.add_holiday(holiday_obj)


    #return total number of holidays (length of inner list)
    def numHolidays(self):
        number_holidays = len(self.inner_holidays)

    #filter holidays by week number & year return as list of holidays
    def filter_holidays_by_week(self, year, week_number):
        global holidays 
        holidays = []
        holidays = list(filter(lambda x: x.date.isocalendar()[0] == year and x.date.isocalendar()[1] == week_number, self.inner_holidays))
        return holidays 

    #get weather and return as string
    def get_weather(self, week, year):
        global weather_week_list
        weather_week_list = []
        global days_week_list
        days_week_list = []
        
        for i in range(1, 8):
            try:
                days = datetime.fromisocalendar(year, week , i)
                days_week_list.append(days)
                timestamp_day = int(datetime.timestamp(days))
                week_range.append(timestamp_day)

            except ValueError:
                print('Please try another week or year.')
        for timestamp in week_range:
            try:
                weather_api = weather_api
                url = (f'http://api.openweathermap.org/data/3.0/onecall/timemachine?lat=44.8041&lon=-93.1669&dt={timestamp}&appid={weather_api}')
                response = requests.get(url)
                json_data = json.loads(response.text)
                global weather_day
                weather_day = json_data['data'][0]['weather'][0]['description']
                weather_week_list.append(weather_day)
            except ValueError:
                print('Oh bother, we cannot seem to find the weather for that date!\nPlease pick another.')
        return weather_week_list

    #view current week and year
    def view_current_week(self):
        global holiday_weather_dict
        today_week = datetime.now().isocalendar().week 
        today_year = datetime.now().year
        self.filter_holidays_by_week(today_year, today_week)
        self.display_holidays_in_week_not_user_input(today_year, today_week)
        while True:
            weather_wanted = input('Would you like to see the weather for today? y/n: ').lower()
            if weather_wanted == 'y':
                for holiday in holidays:
                    date_holiday = holiday.date
                    if date_holiday == datetime.strptime('2022-09-04', '%Y-%m-%d').date():
                        print(f'Weather not found for {holiday}. Sorry!')
                    else:
                        datetime_holiday = datetime.combine(date_holiday, datetime.min.time())
                        timestamp_holiday = int(datetime.timestamp(datetime_holiday))
                        weather_api = weather_api
                        url = weather_website
                        response = requests.get(url)
                        json_data = json.loads(response.text)
                        try:
                            holiday_weather = json_data['data'][0]['weather'][0]['description']
                            print(f'{new_line}{holiday} - {holiday_weather}')
                        except ValueError:
                            print(f'Weather not found for {holiday}. Sorry!')
                break
            elif weather_wanted == 'n':
                break
            else:
                print('Please select either y or n')
                continue
    #display the holidays by week number and year (chosen by user input)
    def display_holidays_in_week_user_input(self):
        global year
        global week_number
        while True:
            make_space('Select a year between 2020-2024 to filter holidays by: ')
            year_input = input('\nSelect a year between 2020-2024 to filter holidays by: ')
            try:
                year = int(year_input)
                if year > 2024 or year < 2020:
                    print('A year within range 2020-2024 please!')
                    continue
                else:  
                    print(f'{new_line}You have chosen the year {str(year)}')
                    break
            except ValueError:
                print('A NUMBER in the range 2020-2024 please!')
                continue
        
        while True:
            week_number_input = input('\nSelect a week number between 1-53 within the selected year to filter holidays by.\nLeave blank for the current week: ') 
            if week_number_input == '' or week_number_input == ' ':
                week_number = datetime.now().isocalendar().week 
                print(f'{new_line}You have chosen the current week, Week #{str(week_number)} in the year {str(year)}')
                self.view_current_week()
                break 
            else:
                try:    
                    week_number = int(week_number_input)
                    if week_number > 53 or week_number < 1:
                        print('A week number within range 1-53 please!')
                        continue
                    else:
                        print(f'{new_line}You have chosen Week #{str(week_number)} in the year {str(year)}')
                        self.filter_holidays_by_week(year, week_number)
                        print(f'{new_line}Here are a list of holidays from Week #{week_number} in the year {year}:{new_line}')
                        for holiday in holidays:
                            print(holiday)
                        break
                except ValueError:
                        print('A number please! No letters or characters.')
                        continue


    #display holidays in week without user input for week and year
    def display_holidays_in_week_not_user_input(self, year, week):
        print(f'{new_line}Here are a list of holidays from Week #{week} in the year {year}:{new_line}')
        for holiday in holidays:
            print(holiday)



#function to begin the program
def intro():
    global inner_holidays_list
    inner_holidays_list = []
    global holiday_list_obj
    holiday_list_obj = HolidayList(inner_holidays_list)
    holiday_list_obj.read_json(json_holidays_file)
    holiday_list_obj.scrape_holidays()
    make_space('Welcome to the Holiday Manager System!')
    make_space('Welcome to the Holiday Manager System!')
    print('\nWelcome to the Holiday Manager System!\n')
    print('Holiday Management\n')
    make_space('Holiday Management')
    print(f'{new_line}There are {len(inner_holidays_list)} holidays currently stored in the system.')


def exit_menu():
    global exit_choice
    print('\nExit\n')
    make_space('Exit')
    while True:
        if exists('holiday-list.json'):
            exit_choice = input('Are you sure you want to exit? [y/n]: ')
            if exit_choice == 'y':
                print('\nGoodbye!')
                break
            elif exit_choice == 'n':
                break
            else:
                print('Select either y or n')
                continue
        else:
            exit_choice = input('Are you sure you want to exit?\nYour changes will be lost.\n[y/n]: ').lower()
            if exit_choice == 'y':
                print('\nGoodbye!')
                break
            elif exit_choice == 'n':
                break
            else:
                print('Select either y or n')
                continue

#function to display main menu and choose option (correctly)
def main_menu():
    while True:
        print('\nHoliday Menu')
        make_space('Holiday Menu')
        main_menu_options = {1: 'Add a Holiday', 2: 'Remove a Holiday', 3: 'Save Holiday List', 4: 'View Holidays', 5: 'Exit'}
        for key in main_menu_options.keys():
            print(f'{key}. {main_menu_options[key]}')
        global main_menu_selection
        try:
            main_menu_selection = int(input('\nSelect a numeric option from the Holiday Menu to continue: '))
            if main_menu_selection > len(main_menu_options):
                print('Nope. Choose a number within Holiday Menu range')
                continue
            elif main_menu_selection < 1:
                print('Nope. Choose a number within Holiday Menu range')
                continue
            elif main_menu_selection == 1:
                holiday_list_obj.user_input_holiday()
                holiday_list_obj.add_holiday(holiday_obj)
                continue
            elif main_menu_selection == 2:
                holiday_list_obj.remove_holiday()
                continue
            elif main_menu_selection == 3:
                holiday_list_obj.save_holiday_list()
                continue
            elif main_menu_selection == 4:
                holiday_list_obj.display_holidays_in_week_user_input()
            elif main_menu_selection == 5:
                exit_menu()
                if exit_choice == 'y':
                    break
                else:
                    continue
        except ValueError:
            print('Nope. Choose a NUMBER within Holiday Menu range')
    print('Thanks for stopping by to check out all the holidays!')



#weather program main code

intro()
main_menu()
