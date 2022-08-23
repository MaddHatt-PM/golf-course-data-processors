import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Button, Entry, Label, Progressbar
from api_usage_tracker import MONTHLY_CAP, add_api_count, compute_cost

from asset_project import ProjectAsset
from datetime import datetime

def create_api_usage_window(requestCost:dict[str, int]=None, command=None, isMainWindow=False):
    if isMainWindow:
        popup = tk.Tk()
    else:
        popup = tk.Toplevel()
        popup.grab_set()
        popup.focus_force()

    popup.title('API Usage')
    popup.resizable(False, False)


    current_cost = compute_cost()
    request_cost = compute_cost(requestCost) if requestCost is not None else 0
    label_text = []
    if request_cost > 0.00001:
        label_text.append('Request Cost: +${}'.format(request_cost))
        label_text.append('New {} Quota: ${} / ${}'.format(datetime.now().strftime('%B'), current_cost + request_cost, MONTHLY_CAP))
    
        if current_cost + request_cost > MONTHLY_CAP:
            label_text.append('Over budget by an estimated ${}.'.format(current_cost + request_cost - MONTHLY_CAP))
            label_text.append('The remainder will be charged to card.')
    
    else:
        label_text.append('Current {} Quota: ${} / ${}'.format(datetime.now().strftime('%B'), current_cost, MONTHLY_CAP))

    label_text = '\n'.join(label_text)
    label = Label(popup, text=label_text, anchor='center')
    label.grid(row=0, column=0, columnspan=2, sticky='nswe', pady=10)


    progbar = Progressbar(popup, orient='horizontal', mode='determinate', length=280)
    progbar['value'] = int(100 * (current_cost + request_cost) / MONTHLY_CAP)
    progbar.grid(sticky='w', row=1, column=0, columnspan=2, padx=5, pady=(5, 15))

    if requestCost is None:
        close_btn = Button(popup, text='Close', command=popup.destroy)
        close_btn.grid(row=2, column=0, columnspan=2, sticky='nswe', padx=5, pady=10)

    else:
        cancel_btn = Button(popup, text='Cancel', command=popup.destroy)
        cancel_btn.grid(row=2, column=0, sticky='nswe', padx=5, pady=10)

        def execute():
            for item in requestCost:
                add_api_count(item, requestCost[item])
            command()
            popup.destroy

        enter_btn = Button(popup, text='Confirm', command=execute)
        enter_btn.grid(row=2, column=1, sticky='nswe', padx=5, pady=10)
        
    if isMainWindow:
        popup.mainloop()

if __name__ == '__main__':
    '''Overbudget example'''
    budget_amt = { "google_elevation": 100000 }
            
    def onclick_overbudget():
        print('Value of 100,000 was added for google_elevation and then removed')
        for key in budget_amt.keys():
            add_api_count(key, budget_amt[key] * -1)

    create_api_usage_window(requestCost=budget_amt, isMainWindow=True, command=onclick_overbudget)

    '''Underbudget example'''
    budget_amt = { "google_elevation": 1 }
            
    def onclick_overbudget():
        print('Value of 100,000 was added for google_elevation and then removed')
        for key in budget_amt.keys():
            add_api_count(key, budget_amt[key] * -1)

    create_api_usage_window(requestCost=budget_amt, isMainWindow=True, command=onclick_overbudget)

    '''Current status example'''
    create_api_usage_window(isMainWindow=True)