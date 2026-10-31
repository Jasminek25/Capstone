from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import os
from kivy.uix.checkbox import CheckBox
from functools import partial
from datetime import date
import datetime
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.properties import ListProperty
import tempfile
import openai
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Load OpenAI API key from environment variable
# CHANGE BELOW LINE SO IT IS ENVIRONMENT VARIABLE INSTEAD OF HARD-CODED
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


class BorderedAnchor(AnchorLayout):
    border_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*self.border_color)
            self._line = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.2)
        self.bind(pos=self._update_line, size=self._update_line, border_color=self._update_color)

    def _update_line(self, *args):
        if getattr(self, '_line', None):
            self._line.rectangle = (self.x, self.y, self.width, self.height)

    def _update_color(self, *args):
        # Rebuild the canvas color if color changes
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.border_color)
            self._line = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.2)


ACCOUNTS_FILE = "accounts.txt"
INVENTORY_FILE = "inventory.txt"
FOOD_SHARE_FILE = "food_share.txt"
DAILY_USAGE_FILE = "daily_usage.txt"


# ---------------- LOGIN SCREEN ----------------
class LoginScreen(Screen):
    # Message displayed on the screen (errors, success messages)
    message = StringProperty("")

    def login(self):
        # Get text from TextInput fields in the KV file
        username = self.ids.username.text
        password = self.ids.password.text

        # If no accounts file exists, tell the user
        if not os.path.exists(ACCOUNTS_FILE):
            self.message = "No accounts found. Create one first."
            return

        # Open the accounts file and check each saved account
        with open(ACCOUNTS_FILE, "r") as file:
            for line in file:
                # Each line is stored as: username,password
                #stored_name, stored_user, stored_pass, stored_business_name, stored_business_type = line.strip().split(",")
                fields = line.strip().split(",")

                stored_user = fields[2]
                stored_pass = fields[3]

                # If login info matches, go to home screen
                if username == stored_user and password == stored_pass:
                    self.manager.current = "home"
                    self.message = ""
                    return

        # If no match was found
        self.message = "Invalid username or password"


# ---------------- CREATE ACCOUNT SCREEN ----------------
class CreateAccountScreen(Screen):
    # Message displayed on the screen
    message = StringProperty("")

    def create_account(self):
        # Get user input from TextInput fields
        name = self.ids.new_name.text
        username = self.ids.new_username.text
        password = self.ids.new_password.text
        email = self.ids.new_email.text
        business_name = self.ids.new_business_name.text
        business_type = self.ids.new_business_type.text

        # Check if fields are empty
        if not username or not password:
            self.message = "Please fill in all fields"
            return
        
         # Open file in append mode to add a new account
        with open(ACCOUNTS_FILE, "a") as file:
            file.write(f"{name},{email},{username},{password},{business_name},{business_type}\n")

        # Success message
        self.message = "Account created! Go back to login."

# ---------------- HOME SCREEN ----------------
class HomeScreen(Screen):
    # No logic here yet, just UI
    
    pass


# ---------------- Inventory SCREEN ----------------
class InventoryScreen(Screen):
    # No logic here yet, just UI
    pass

# ---------------- Add Inventory SCREEN ----------------
class AddInventoryScreen(Screen):
    message = StringProperty("")

    def submit_inventory(self):
        # Get user input from TextInput fields
        ingredient = self.ids.new_ingredient.text
        amount_bought = self.ids.new_amount_bought.text
        last_bought = self.ids.new_last_bought.text
        expiry_date = self.ids.new_expiry_date.text

        # Check if fields are empty
        if not ingredient or not amount_bought or not last_bought or not expiry_date:
            self.message = "Please fill in all fields"
            return

        # Open file in append mode to add a new inventory item
        with open("inventory.txt", "a") as file:
            file.write(f"{ingredient},{amount_bought},{last_bought},{expiry_date}\n")

        # Success message
        self.message = "Inventory item added!"
        # Clear the input fields so user can add another item
        try:
            self.ids.new_ingredient.text = ""
            self.ids.new_amount_bought.text = ""
            self.ids.new_last_bought.text = ""
            self.ids.new_expiry_date.text = ""
            # Set focus back to the first field for convenience
            self.ids.new_ingredient.focus = True
        except Exception:
            pass




# ---------------- See Inventory SCREEN ----------------
class SeeInventoryScreen(Screen):
    def on_pre_enter(self):
        # Populate the inventory grid from the inventory file each time the screen is shown
        grid = self.ids.get("inventory_grid")
        if not grid:
            return
        grid.clear_widgets()

        # Header row
        header = BoxLayout(size_hint_y=None, height=40)
        header.add_widget(Label(markup=True, text='[b]Ingredient[/b]', size_hint_x=0.3))
        header.add_widget(Label(markup=True, text='[b]Amount Bought (oz)[/b]', size_hint_x=0.2))
        header.add_widget(Label(markup=True, text='[b]Last Bought[/b]', size_hint_x=0.25))
        header.add_widget(Label(markup=True, text='[b]Expiry Date[/b]', size_hint_x=0.25))
        grid.add_widget(header)

        # If inventory file doesn't exist or is empty, show a friendly message
        if not os.path.exists(INVENTORY_FILE):
            grid.add_widget(Label(text="No inventory found.", size_hint_y=None, height=40))
            return

        with open(INVENTORY_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            grid.add_widget(Label(text="No inventory items.", size_hint_y=None, height=40))
            return

        # Create a row for each inventory item
        for line in lines:
            parts = line.split(",")
            ingredient = parts[0] if len(parts) > 0 else ""
            amount_bought = parts[1] if len(parts) > 1 else ""
            last_bought = parts[2] if len(parts) > 2 else ""
            expiry = parts[3] if len(parts) > 3 else ""

            row = BoxLayout(size_hint_y=None, height=36)
            row.add_widget(Label(text=ingredient, size_hint_x=0.3))
            row.add_widget(Label(text=amount_bought, size_hint_x=0.2))
            row.add_widget(Label(text=last_bought, size_hint_x=0.25))
            row.add_widget(Label(text=expiry, size_hint_x=0.25))
            grid.add_widget(row)

# ---------------- UpdateInventoryExpiryScreen SCREEN ----------------
class UpdateInventoryExpiryScreen(Screen):
    def parse_date(self, date_str):
        # Try common date formats (ISO, m/d/Y, d/m/Y) and two-digit years.
        # Prefer month/day when ambiguous (US style) by trying %m/%d before %d/%m.
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%d/%m/%y"):
            try:
                return datetime.datetime.strptime(date_str.strip(), fmt).date()
            except Exception:
                continue
        return None

    def on_pre_enter(self):
        grid = self.ids.get("expiry_grid")
        if not grid:
            return
        grid.clear_widgets()

        # Header
        header = BoxLayout(size_hint_y=None, height=40)
        header.add_widget(Label(markup=True, text='[b]Action Taken[/b]', size_hint_x=0.15))
        header.add_widget(Label(markup=True, text='[b]Ingredient[/b]', size_hint_x=0.65))
        header.add_widget(Label(markup=True, text='[b]Expiry Date[/b]', size_hint_x=0.2))
        grid.add_widget(header)

        if not os.path.exists(INVENTORY_FILE):
            grid.add_widget(Label(text="No inventory found.", size_hint_y=None, height=40))
            return

        today = datetime.date.today()
        week_ahead = today + datetime.timedelta(days=7)

        with open(INVENTORY_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        found = False
        for line in lines:
            parts = line.split(",")
            ingredient = parts[0] if len(parts) > 0 else ""
            expiry_raw = parts[3] if len(parts) > 3 else ""
            expiry_date = self.parse_date(expiry_raw)
            if not expiry_date:
                continue

            # Include items expiring within the next 7 days (including today)
            if today <= expiry_date <= week_ahead:
                found = True
                row = BoxLayout(size_hint_y=None, height=36)
                # add a small left spacer so the checkbox and ingredient shift right
                row.add_widget(Widget(size_hint_x=None, width=dp(12)))
                # Use a dedicated bordered AnchorLayout so each container manages its own canvas
                container = BorderedAnchor(size_hint_x=None, width=dp(48), anchor_x='center', anchor_y='center')
                cb = CheckBox(size_hint=(None, None), size=(dp(28), dp(28)))
                cb.bind(active=partial(self._on_checked, ingredient, expiry_raw, row))
                container.add_widget(cb)
                row.add_widget(container)
                # Center the ingredient text under the header column
                ing_anchor = AnchorLayout(size_hint_x=0.65, anchor_x='center', anchor_y='center')
                ing_label = Label(text=ingredient, size_hint=(None, None))
                ing_anchor.add_widget(ing_label)
                row.add_widget(ing_anchor)
                # Center the expiry date as well
                exp_anchor = AnchorLayout(size_hint_x=0.2, anchor_x='center', anchor_y='center')
                exp_label = Label(text=expiry_raw, size_hint=(None, None))
                exp_anchor.add_widget(exp_label)
                row.add_widget(exp_anchor)
                grid.add_widget(row)

        if not found:
            grid.add_widget(Label(text="No items expiring within a week.", size_hint_y=None, height=40))

    def _on_checked(self, ingredient, expiry_raw, row, checkbox, value):
        # When checkbox becomes active (checked), remove item from inventory file and UI
        if not value:
            return
        # Remove matching lines (ingredient + expiry)
        try:
            if not os.path.exists(INVENTORY_FILE):
                return
            with open(INVENTORY_FILE, "r") as f:
                lines = [l for l in f if l.strip()]

            retained = []
            removed_any = False
            for l in lines:
                parts = l.strip().split(",")
                name = parts[0] if len(parts) > 0 else ""
                exp = parts[2] if len(parts) > 2 else ""
                if name == ingredient and exp == expiry_raw:
                    removed_any = True
                    continue
                retained.append(l)

            if removed_any:
                with open(INVENTORY_FILE, "w") as f:
                    f.writelines(retained)

            # Remove the row from the grid
            parent = row.parent
            if parent:
                parent.remove_widget(row)
        except Exception:
            pass





# ---------------- UsageManagementScreen SCREEN ----------------
class UsageManagementScreen(Screen):
    # No logic here yet, just UI
    pass

# ---------------- Daily Usage SCREEN ----------------
class UsageReport(Screen):
    def on_pre_enter(self):
        # Populate the usage grid from the daily usage file each time the screen is shown
        grid = self.ids.get("usage_grid")
        if not grid:
            return
        grid.clear_widgets()

        # Header row
        header = BoxLayout(size_hint_y=None, height=40)
        header.add_widget(Label(markup=True, text='[b]Ingredient[/b]', size_hint_x=0.5))
        header.add_widget(Label(markup=True, text='[b]Quantity[/b]', size_hint_x=0.25))
        header.add_widget(Label(markup=True, text='[b]Date[/b]', size_hint_x=0.25))
        grid.add_widget(header)

        # If daily usage file doesn't exist or is empty, show a friendly message
        if not os.path.exists(DAILY_USAGE_FILE):
            grid.add_widget(Label(text="No usage reports found.", size_hint_y=None, height=40))
            return

        with open(DAILY_USAGE_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            grid.add_widget(Label(text="No usage entries.", size_hint_y=None, height=40))
            return

        # Create a row for each usage entry (expected format: ingredient,quantity,date)
        for line in lines:
            parts = line.split(",")
            ingredient = parts[0] if len(parts) > 0 else ""
            quantity = parts[1] if len(parts) > 1 else ""
            date = parts[2] if len(parts) > 2 else ""

            row = BoxLayout(size_hint_y=None, height=36)
            row.add_widget(Label(text=ingredient, size_hint_x=0.5))
            row.add_widget(Label(text=quantity, size_hint_x=0.25))
            row.add_widget(Label(text=date, size_hint_x=0.25))
            grid.add_widget(row)

# ---------------- Usage charts SCREEN ----------------
class UsageChartsScreen(Screen):
    def on_pre_enter(self):
        # Parse and store all data for month filtering
        self.all_data = {}
        self.dates_set = set()
        
        if not MATPLOTLIB_AVAILABLE or not os.path.exists(DAILY_USAGE_FILE):
            return
        
        # Parse file
        with open(DAILY_USAGE_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < 3:
                    continue
                ingredient = parts[0]
                qty_raw = parts[1]
                date_raw = parts[2]
                
                try:
                    qty = float(qty_raw.replace(',', ''))
                except Exception:
                    continue
                
                try:
                    dt = datetime.datetime.strptime(date_raw, '%m/%d/%y').date()
                except Exception:
                    try:
                        dt = datetime.datetime.strptime(date_raw, '%m/%d/%Y').date()
                    except Exception:
                        continue
                
                self.dates_set.add(dt)
                self.all_data.setdefault(ingredient, {}).setdefault(dt, 0.0)
                self.all_data[ingredient][dt] += qty
        
        # Generate chart for all data initially
        self.generate_chart_for_month('All Months')
        
        # Reset spinner to "All Months"
        try:
            spinner = self.ids.get('month_spinner')
            if spinner:
                spinner.text = 'All Months'
        except Exception:
            pass
    
    def on_month_selected(self, month_name):
        """Called when user selects a month from the spinner"""
        self.generate_chart_for_month(month_name)
    
    def generate_chart_for_month(self, month_name):
        """Generate chart filtered by month"""
        if not self.all_data:
            return
        
        # Map month names to month numbers
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'All Months': None
        }
        
        selected_month = month_map.get(month_name)
        
        # Filter data for the selected month
        filtered_data = {}
        for ingredient, series in self.all_data.items():
            filtered_series = {}
            for dt, qty in series.items():
                if selected_month is None or dt.month == selected_month:
                    filtered_series[dt] = qty
            if filtered_series:
                filtered_data[ingredient] = filtered_series
        
        # If no data for this month, clear the chart
        if not filtered_data:
            try:
                img = self.ids.get('chart_image')
                if img:
                    img.source = ''
            except Exception:
                pass
            return
        
        # Get sorted dates for filtered data
        dates_set = set()
        for ingredient, series in filtered_data.items():
            dates_set.update(series.keys())
        dates = sorted(dates_set)
        
        if not dates:
            try:
                img = self.ids.get('chart_image')
                if img:
                    img.source = ''
            except Exception:
                pass
            return
        
        # Prepare plot with larger width for better x-axis spacing
        fig, ax = plt.subplots(figsize=(14, 6))
        for ingredient, series in filtered_data.items():
            y = [series.get(d, 0.0) for d in dates]
            ax.plot(dates, y, marker='o', label=ingredient)

        if month_name == 'All Months':
            # Group by month for x-axis
            import calendar
            # Build a mapping: (year, month) -> sum for each ingredient
            month_labels = []
            month_indices = []
            month_data = {}
            for d in dates:
                ym = (d.year, d.month)
                if ym not in month_data:
                    month_data[ym] = {ing: 0.0 for ing in filtered_data.keys()}
                    month_labels.append(f"{calendar.month_abbr[d.month]} {d.year}")
                    month_indices.append(ym)
                for ing in filtered_data.keys():
                    month_data[ym][ing] += filtered_data[ing].get(d, 0.0)
            # Plot by month
            ax.clear()
            for ing in filtered_data.keys():
                y = [month_data[ym][ing] for ym in month_indices]
                ax.plot(month_labels, y, marker='o', label=ing)
            ax.set_xlabel('Month')
            ax.set_title('Monthly Usage (All Months)')
            ax.legend()
        else:
            ax.set_xlabel('Date')
            ax.set_title(f'Daily Usage - {month_name}')
            # Format x-axis to show dates with better spacing
            try:
                import matplotlib.dates as mdates
                num_dates = len(dates)
                if num_dates > 10:
                    interval = max(2, num_dates // 10)
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
                else:
                    ax.xaxis.set_major_locator(mdates.DayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            except Exception:
                pass
            fig.autofmt_xdate()
        ax.set_ylabel('Ounces used')
        plt.tight_layout()

        # Save and display
        tmp = os.path.join(tempfile.gettempdir(), 'usage_chart.png')
        fig.savefig(tmp, bbox_inches='tight')
        plt.close(fig)

        try:
            img = self.ids.get('chart_image')
            if img:
                img.source = tmp
                img.reload()
        except Exception:
            pass

# ---------------- Future Usage Projection Screen ----------------
class FutureUsageProjectionScreen(Screen):

    def _call_openai_api(self, prompt):
        """Raw HTTPS call to OpenAI — no SDK version issues."""
        if not OPENAI_API_KEY:
            print("ERROR: OPENAI_API_KEY is not set or is empty")
            return None
        print(f"DEBUG: API key found, starts with: {OPENAI_API_KEY[:8]}...")
        try:
            import json
            from http.client import HTTPSConnection
            payload = json.dumps({
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }).encode("utf-8")
            conn = HTTPSConnection("api.openai.com", timeout=20)
            conn.request("POST", "/v1/chat/completions", body=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            })
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            print(f"DEBUG: OpenAI response status: {resp.status}")
            print(f"DEBUG: OpenAI response body: {body[:300]}")
            result = json.loads(body)
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI error: {e}")
            return None
    
    def on_pre_enter(self):
        """Generate chart on entry, report only on button press."""
        if not MATPLOTLIB_AVAILABLE or not os.path.exists(DAILY_USAGE_FILE):
            return
        self.historical_data = self._parse_historical_data()
        if not self.historical_data:
            return
        projection_data = self._fallback_projection()
        self._render_chart(projection_data, used_ai=False)

    def _parse_historical_data(self):
        data = {}
        try:
            with open(DAILY_USAGE_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) < 3:
                        continue
                    ingredient, qty_raw = parts[0], parts[1]
                    try:
                        qty = float(qty_raw.replace(',', ''))
                    except Exception:
                        continue
                    data.setdefault(ingredient, []).append(qty)
        except Exception:
            pass
        return data

    def _fallback_projection(self):
        result = {}
        for ingredient, quantities in self.historical_data.items():
            avg = sum(quantities) / len(quantities)
            result[ingredient] = round(avg * 30, 1)
        return result

    def _call_openai_api(self, prompt):
        """Raw HTTPS call to OpenAI — no SDK version issues."""
        if not OPENAI_API_KEY:
            return None
        try:
            import json
            from http.client import HTTPSConnection
            payload = json.dumps({
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }).encode("utf-8")
            conn = HTTPSConnection("api.openai.com", timeout=20)
            conn.request("POST", "/v1/chat/completions", body=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            })
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI error: {e}")
            return None

    def _build_report_prompt(self):
        lines = []
        for ingredient, quantities in self.historical_data.items():
            avg = sum(quantities) / len(quantities)
            trend = "increasing" if quantities[-1] > quantities[0] else "decreasing" if quantities[-1] < quantities[0] else "stable"
            lines.append(
                f"- {ingredient}: {len(quantities)} recorded uses, "
                f"avg {avg:.2f} oz/day, trend is {trend}, "
                f"values: {quantities}"
            )
        history_block = "\n".join(lines)

        return f"""You are an AI inventory agent for a food business.
Analyze the following historical daily ingredient usage data and generate a clear business report.

Historical Usage Data:
{history_block}

Your report must include:
1. USAGE SUMMARY: Brief overview of each ingredient's usage pattern
2. 30-DAY PROJECTIONS: Predicted total usage (oz) for each ingredient over the next 30 days
3. TREND ANALYSIS: Which ingredients are increasing, decreasing, or stable in usage
4. RISK FLAGS: Any ingredients that may run short or be over-ordered based on trends
5. RECOMMENDATIONS: Specific action items for the business (order more, reduce order, watch closely)

Write in clear, professional business language. Be specific with numbers."""

    def run_ai_agent(self):
        """Called when the user presses the AI Report button."""
        if not OPENAI_API_KEY:
            try:
                report_label = self.ids.get('report_label')
                if report_label:
                    report_label.text = "ERROR: No OpenAI API key found.\nSet OPENAI_API_KEY environment variable and restart the app."
            except Exception:
                pass
            return

        try:
            report_label = self.ids.get('report_label')
            if report_label:
                report_label.text = "AI Agent is analyzing your usage data...\nPlease wait (10-20 seconds)."
        except Exception:
            pass

        import threading
        thread = threading.Thread(target=self._agent_task, daemon=True)
        thread.start()

    def _agent_task(self):
        """Runs in background: calls AI, gets projection + report, renders both."""
        import json, re

        # ---- Step 1: Get structured JSON projection ----
        json_prompt = f"""Analyze this ingredient usage data and return ONLY a JSON object 
with 30-day projected totals in oz. No explanation, no markdown.
Format: {{"ingredient": projected_oz, ...}}

Data:
""" + "\n".join([f"- {k}: {v}" for k, v in self.historical_data.items()])

        projection_data = None
        content = self._call_openai_api(json_prompt)
        if content:
            try:
                projection_data = json.loads(content)
            except Exception:
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    try:
                        projection_data = json.loads(match.group(0))
                    except Exception:
                        pass
            if projection_data:
                try:
                    projection_data = {k: float(v) for k, v in projection_data.items()}
                except Exception:
                    projection_data = None

        if not projection_data:
            projection_data = self._fallback_projection()

        # ---- Step 2: Get written AI report ----
        report_prompt = self._build_report_prompt()
        report_text = self._call_openai_api(report_prompt)
        if not report_text:
            report_text = "AI report unavailable. Showing average-based projections.\n\n"
            for ingredient, total in projection_data.items():
                report_text += f"  {ingredient}: {total:.0f} oz projected over 30 days\n"

        # ---- Step 3: Schedule UI update on main thread ----
        from kivy.clock import Clock
        Clock.schedule_once(
            lambda dt: self._update_ui(projection_data, report_text, used_ai=bool(content)),
            0
        )

    def _update_ui(self, projection_data, report_text, used_ai):
        """Update chart and report label on the main thread."""
        self._render_chart(projection_data, used_ai)
        try:
            report_label = self.ids.get('report_label')
            if report_label:
                report_label.text = report_text
        except Exception:
            pass

    def _render_chart(self, projection_data, used_ai):
        import tempfile
        fig, ax = plt.subplots(figsize=(10, 5))
        ingredients = list(projection_data.keys())
        quantities = list(projection_data.values())
        color = 'steelblue' if used_ai else 'slategray'
        bars = ax.bar(ingredients, quantities, color=color, edgecolor='black')
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.0f} oz', ha='center', va='bottom', fontsize=9)
        source = "AI (GPT-3.5)" if used_ai else "Average Fallback"
        ax.set_xlabel('Ingredient', fontsize=12)
        ax.set_ylabel('Projected Usage (oz) — Next 30 Days', fontsize=12)
        ax.set_title(f'30-Day Usage Projection  [{source}]', fontsize=14)
        plt.tight_layout()
        tmp = os.path.join(tempfile.gettempdir(), 'future_projection_chart.png')
        fig.savefig(tmp, bbox_inches='tight')
        plt.close(fig)
        try:
            img = self.ids.get('projection_chart_image')
            if img:
                img.source = tmp
                img.reload()
        except Exception:
            pass






# ---------------- FOOD SHARE SCREEN ----------------
class FoodShareScreen(Screen):
    # No logic here yet, just UI
    message = StringProperty("")

    def submit_food_share(self):
        items = self.ids.new_items.text
        location = self.ids.new_location.text
        location_email = self.ids.new_location_email.text
        driver = self.ids.new_driver.text
        time = self.ids.new_time.text
        # Check if fields are empty
        if not items or not location or not location_email or not driver or not time:
            self.message = "Please fill in all fields"
            return
        
        # Food share submission logic
        with open(FOOD_SHARE_FILE, "a") as file:
            file.write(f"{items},{location},{location_email},{driver},{time}\n")
        
        self.message = "Food share submitted!"

        try:
            self.ids.new_items.text = ""
            self.ids.new_location.text = ""
            self.ids.new_location_email.text = ""
            self.ids.new_driver.text = ""
            self.ids.new_time.text = ""
            # Set focus back to the first field for convenience
            self.ids.new_items.focus = True
        except Exception:
            # If ids aren't available for some reason, ignore silently
            pass




# ---------------- MAIN APP ----------------
class SmartSave(App):
    def build(self):
        # ScreenManager controls which screen is shown
        sm = ScreenManager()

        # Add all screens to the manager
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(CreateAccountScreen(name="create"))

        sm.add_widget(HomeScreen(name="home"))

        sm.add_widget(InventoryScreen(name="inventory_main"))
        sm.add_widget(AddInventoryScreen(name="add_inventory"))
        sm.add_widget(SeeInventoryScreen(name="see_inventory"))
        sm.add_widget(UpdateInventoryExpiryScreen(name="update_expired_inventory"))

        sm.add_widget(UsageManagementScreen(name="usage_management"))
        sm.add_widget(UsageReport(name="usage_report"))
        sm.add_widget(UsageChartsScreen(name="usage_charts"))
        sm.add_widget(FutureUsageProjectionScreen(name="future_projection"))


        sm.add_widget(FoodShareScreen(name="food_share"))

        # Return the screen manager as the main app widget
        return sm


# Run the app
if __name__ == "__main__":
    SmartSave().run()