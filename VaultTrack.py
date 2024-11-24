import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import requests
import currency_module
import os
import pickle

# File path for saving expenses
SAVE_FILE = "expenses_data.pkl"
def get_forex_rate(currency):
    # Fetches gold and silver prices based on the selected currency
    url_gold = 'https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/'+currency
    url_silver = 'https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAG/'+currency
    
    gold_price = silver_price = None  # Initialize prices
    try:
        response = requests.get(url_gold)  # Request gold price
        response_silver = requests.get(url_silver)  # Request silver price
        
        # Raise exceptions for HTTP errors
        response.raise_for_status()
        response_silver.raise_for_status()

        # Parse JSON responses
        data = response.json()
        data_silver = response_silver.json()

        # Get the bid prices for gold and silver
        gold_price = data[1]['spreadProfilePrices'][0]['bid']
        silver_price = data_silver[1]['spreadProfilePrices'][0]['bid']

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
      
    return gold_price, silver_price

# Class to represent an Expense entry
class Expense:
    def __init__(self, ounces, cost, date, transaction_currency,selected_metal,metal_index):
        self.ounces = ounces  # Amount of precious metal in ounces
        self.cost = cost  # Category of the transaction
        self.date = date  # Date of the transaction
        self.transaction_currency = transaction_currency  # Currency used
        self.selected_metal=selected_metal
        self.metal_index=metal_index
    # Class to manage the Vault Tracker GUI and logic
class VaultTracker:
    def __init__(self, root):
        # Initialize the main window and variables
        self.root = root
        self.root.title("Expense Tracker")
     
        # List to store the expenses because of dynamic memory management during runtime list is used for fast removal and adittion 
        self.expenses = []
        # Load expenses from the file
        self.load_expenses()
        # Create labels for gold and silver prices
        self.label_gold = tk.Label(root, text=f"Count: {1}", font=("Arial", 24))
        self.label_silver = tk.Label(root, text=f"Count: {1}", font=("Arial", 24))

        # Create list boxes for currency and metal selection
        self.currency_list = tk.Listbox(root, height=5)
        self.metal_list = tk.Listbox(root, height=2)
        self.selected_metal =   "GOLD"
        self.selected_currency = "USD"
        self.metal_index =   0
        self.currency_index = 0
        # Setup the GUI components
        self.setup_gui()

    # Setup the user interface elements
    def setup_gui(self):
        # Metal Entry    
        tk.Label(self.root, text="Select Metal:").grid(row=0, column=0, padx=10, pady=5)
        self.metal_list.grid(row=0, column=1, padx=10, pady=5)
        
        # Populate the metal listbox
        for metal in currency_module.precious_metals:
            self.metal_list.insert(tk.END, metal)  # Use tk.END to append items
        
        self.metal_list.select_set(0)  # Preselect the first metal (Gold)
        # Cost entry field
        tk.Label(self.root, text="Cost:").grid(row=1, column=0, padx=10, pady=5)
        self.cost = tk.Entry(self.root)
        self.cost.grid(row=1, column=1, padx=10, pady=5)

        # Ounces entry field
        tk.Label(self.root, text="Ounces:").grid(row=2, column=0, padx=10, pady=5)
        self.ounces = tk.Entry(self.root)
        self.ounces.grid(row=2, column=1, padx=10, pady=5)

        # Date entry field with input validation
        self.date_var = tk.StringVar(self.root)
        self.date_var.trace_add("write", self.format_date)  # Track input changes

        tk.Label(self.root, text="Date (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=5)
        self.date_entry = tk.Entry(self.root, textvariable=self.date_var)
        self.date_entry.grid(row=3, column=1, padx=10, pady=5)

        # Add buttons to add and view expenses
        self.add_button = tk.Button(self.root, text="Add Expense", command=self.add_expense)
        self.add_button.grid(row=4, column=0, columnspan=2, pady=10)

        self.view_button = tk.Button(self.root, text="View Expenses", command=self.view_expenses)
        self.view_button.grid(row=5, column=0, columnspan=2, pady=10)

        self.summary_button = tk.Button(self.root, text="View Summary", command=self.view_summary)
        self.summary_button.grid(row=6, column=0, columnspan=2, pady=10)

        # Display gold and silver price labels
        self.label_gold.grid(row=7, column=0, columnspan=2, pady=10)
        self.label_silver.grid(row=8, column=0, columnspan=2, pady=10)

        # Currency list selection
        self.currency_list.grid(row=9, column=0, columnspan=2, pady=10)
        for currency in currency_module.currencies:
            self.currency_list.insert(tk.END, currency)
        self.currency_list.select_set(2)  # Default selection
        # Bind selections to separate functions
        self.metal_list.bind('<<ListboxSelect>>', self.on_metal_select)
        self.currency_list.bind('<<ListboxSelect>>', self.on_currency_select)
        # Add a button to remove expenses
        self.remove_button = tk.Button(self.root, text="Remove Expense", command=self.remove_expense)
        self.remove_button.grid(row=6, column=2, columnspan=2, pady=10)
    # Show current gold and silver prices
    def show_gold(self):
        # Fetch the selected currency and update the prices
        selected_currency = self.selected_currency
        self.g_price, self.s_price = get_forex_rate(selected_currency)

        # Update gold and silver labels
        self.label_gold.config(text=f"Gold price 1oz: {currency_module.currency_symbols[selected_currency]}{self.g_price}")
        self.label_silver.config(text=f"Silver price 1oz: {currency_module.currency_symbols[selected_currency]}{self.s_price}")

        # Refresh the price every 500ms
        self.root.after(500, self.show_gold)
    def on_metal_select(self, event):
        selection = self.metal_list.curselection()
        
        if len(selection) != 0:  # Ensure something is selected
            self.metal_index=selection[0]
            self.selected_metal = self.metal_list.get(selection)
            
    def on_currency_select(self, event):
        selected_currency = self.currency_list.curselection()
        if len(selected_currency) != 0:
            self.currency_index=selected_currency[0]
            self.selected_currency=self.currency_list.get(selected_currency)
            
    # Add a new expense to the list
    def add_expense(self):
        try:
            # Get input values from the form
            cost = float(self.cost.get())
            ounces = float(self.ounces.get())
            date = self.date_entry.get()
            transaction_currency = self.selected_currency
                                     
            selected_metal = self.selected_metal
            
            # Ensure all fields are filled out
            if not ounces or not date or not transaction_currency:
                raise ValueError("Ounces and date must not be empty.")
            
            # Create a new Expense object and add it to the list
            expense = Expense(ounces, cost, date, transaction_currency,selected_metal,self.metal_index)
            self.expenses.append(expense)
             # Save expenses to file after adding
            self.save_expenses()
            # Show success message
            messagebox.showinfo("Success", f"Added expense: {ounces:.2f} ounces of {selected_metal}  for {currency_module.currency_symbols[transaction_currency]}{cost:.2f} on {date} in {transaction_currency}.")
            self.clear_entries()  # Clear form after adding

        except ValueError as e:
            # Show error if input is invalid
            messagebox.showerror("Error", f"Invalid input: {e}")

    # View all recorded expenses
    def view_expenses(self):
        if not self.expenses:
            messagebox.showinfo("Expenses", "No expenses recorded.")
            return
        
        # Display all expenses in a message box
        expenses_str = "\n".join(f"{e.ounces:.2f} ounces of {e.selected_metal}  for {currency_module.currency_symbols[e.transaction_currency]}{e.cost} on {e.date} in {e.transaction_currency}" for e in self.expenses)
        messagebox.showinfo("Expenses", expenses_str)

    # View a summary of expenses by category
    def view_summary(self):
        if not self.expenses:
            messagebox.showinfo("Summary", "No expenses recorded.")
            return
        # Current prices of gold and silver in the selected currency
        metals_cost = [self.g_price, self.s_price]

        # Dictionary to store total worth, gain, and loss per currency
        summary_data = {}

        # Loop through each expense to calculate total worth and gain/loss by currency
        for expense in self.expenses:
            metal_index = expense.metal_index
            current_price = metals_cost[metal_index]

            # Get the purchase price in the transaction's currency
            purchase_cost = expense.cost
            current_value = expense.ounces * current_price

            # Calculate gain or loss for this transaction
            if current_price > purchase_cost:
                gain = (current_price - purchase_cost) * expense.ounces
                loss = 0
            else:
                gain = 0
                loss = (purchase_cost - current_price) * expense.ounces

            # Add the results to the correct currency in summary_data
            currency = expense.transaction_currency
            if currency not in summary_data:
                summary_data[currency] = {
                    'total_worth': 0,
                    'total_gain': 0,
                    'total_loss': 0
                }

            summary_data[currency]['total_worth'] += current_value
            summary_data[currency]['total_gain'] += gain
            summary_data[currency]['total_loss'] += loss

        # Create summary string with total worth, gain, and loss for each currency
        summary_lines = []
        for currency, data in summary_data.items():
            summary_lines.append(
                f"{currency_module.currency_symbols[currency]} - "
                f"Total worth: {data['total_worth']:.2f}, "
                f"Gain: {data['total_gain']:.2f}, "
                f"Loss: {data['total_loss']:.2f}"
            )

        # Join the summary lines and show the final summary
        summary = "\n".join(summary_lines)
        messagebox.showinfo("Summary", summary)


    # Clear input fields
    def clear_entries(self):
        self.cost.delete(0, tk.END)
        self.ounces.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)

    # Automatically format the date input field
    def format_date(self, *args):
        current_text = self.date_var.get()

        # Remove any invalid characters
        filtered_text = "".join([char for char in current_text if char.isdigit() or char == "-"])
        filtered_text = filtered_text.replace("-", "")

        # Insert dashes at the right positions for YYYY-MM-DD format
        if len(filtered_text) > 4:
            filtered_text = filtered_text[:4] + "-" + filtered_text[4:]
        if len(filtered_text) > 6:
            filtered_text = filtered_text[:7] + "-" + filtered_text[7:]

        # Ensure the date format is no longer than 10 characters
        formatted_text = filtered_text[:10]

        # Prevent infinite loop by only updating if needed
        if self.date_var.get() != formatted_text:
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, formatted_text)
            self.date_entry.icursor(tk.END)  # Move cursor to the end of the text
    def remove_expense(self):
        if not self.expenses:
            messagebox.showinfo("Remove Expense", "No expenses recorded to remove.")
            return
        
        # Display expenses with their respective indices
        expenses_str = "\n".join(f"{i}: {e.ounces:.2f} ounces of {e.selected_metal} for {currency_module.currency_symbols[e.transaction_currency]}{e.cost} on {e.date} in {e.transaction_currency}"
                                for i, e in enumerate(self.expenses))
        
        # Ask the user for the index of the expense to remove
        expense_to_remove =  simpledialog.askinteger("Remove Expense", f"Select the index of the expense to remove:\n\n{expenses_str}")
        
        # Ensure valid index is selected
        if expense_to_remove is not None and 0 <= expense_to_remove < len(self.expenses):
            removed_expense = self.expenses.pop(expense_to_remove)
            # Save expenses to file after removing
            self.save_expenses()
            messagebox.showinfo("Success", f"Removed expense: {removed_expense.ounces:.2f} ounces of {removed_expense.selected_metal} on {removed_expense.date}.")
        else:
            messagebox.showerror("Error", "Invalid expense index.") 
    def save_expenses(self):
        try:
            with open(SAVE_FILE, 'wb') as f:
                pickle.dump(self.expenses, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save expenses: {e}")
    def load_expenses(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'rb') as f:
                    self.expenses = pickle.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load expenses: {e}")
        else:
            self.expenses = []  # Initialize with an empty list if no file exists

# Main application entry point
if __name__ == "__main__":
    root = tk.Tk()  # Create the main window
    app = VaultTracker(root)  # Initialize the app
    app.show_gold()  # Start showing gold prices
    root.mainloop()  # Start the Tkinter event loop
