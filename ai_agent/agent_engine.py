import frappe
import json
import requests
from frappe.utils import nowdate, flt, now_datetime


class AIAgentEngine:
    def __init__(self):
        try:
            self.settings = frappe.get_single("AI Agent Settings")
            self.api_key = self.settings.api_key or ""
            self.model = self.settings.model_name or "glm-4-flash"
            self.provider = self.settings.api_provider or "Z.ai"
            self.company = self.settings.default_company or ""
        except:
            self.api_key = ""
            self.model = "glm-4-flash"
            self.provider = "Z.ai"
            self.company = ""
    
    # ==========================================
    # 🧠 التواصل مع الـ AI
    # ==========================================
    
    def call_ai(self, system_prompt, user_message):
        if not self.api_key or "placeholder" in self.api_key.lower():
            return "⚠️ API Key غير مضبوط. راجع AI Agent Settings وضع مفتاح API صحيح."
        
        if self.provider == "Z.ai":
            return self._call_zai(system_prompt, user_message)
        elif self.provider == "Gemini":
            return self._call_gemini(system_prompt, user_message)
        elif self.provider == "OpenAI":
            return self._call_openai(system_prompt, user_message)
        elif self.provider == "Anthropic":
            return self._call_anthropic(system_prompt, user_message)
        else:
            return self._call_zai(system_prompt, user_message)
    
    def _call_zai(self, system_prompt, user_message):
        """التواصل مع Z.ai (Zhipu AI) - متوافق مع OpenAI API"""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4/"
            )
            
            response = client.chat.completions.create(
                model=self.model or "glm-4-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            frappe.log_error(f"AI Agent Z.ai Error: {str(e)}")
            return f"❌ خطأ في الاتصال بـ Z.ai: {str(e)}"
    
    def _call_gemini(self, system_prompt, user_message):
        """التواصل مع Google Gemini"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": system_prompt + "\n\n" + user_message}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if "candidates" in result:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            elif "error" in result:
                return f"❌ خطأ: {result['error'].get('message', 'Unknown error')}"
            else:
                return f"❌ خطأ غير متوقع: {str(result)[:200]}"
        
        except Exception as e:
            frappe.log_error(f"AI Agent Gemini Error: {str(e)}")
            return f"❌ خطأ في الاتصال بـ Gemini: {str(e)}"
    
    def _call_openai(self, system_prompt, user_message):
        """التواصل مع OpenAI"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
            frappe.log_error(f"AI Agent OpenAI Error: {str(e)}")
            return f"❌ خطأ في الاتصال بـ OpenAI: {str(e)}"
    
    def _call_anthropic(self, system_prompt, user_message):
        """التواصل مع Anthropic Claude"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except Exception as e:
            frappe.log_error(f"AI Agent Anthropic Error: {str(e)}")
            return f"❌ خطأ في الاتصال بـ Anthropic: {str(e)}"
    
    # ==========================================
    # 📄 معالجة فواتير المشتريات
    # ==========================================
    
    def process_purchase_invoice(self, invoice_data):
        accounting_context = self._build_accounting_context()
        system_prompt = f"""أنت محاسب ذكي متصل بنظام ERPNext.
بيانات الحسابات المتاحة:
{json.dumps(accounting_context, ensure_ascii=False, indent=2)}
مهمتك:
1. تحليل بيانات الفاتورة الواردة
2. تحديد الحساب المحاسبي الصحيح لكل صنف
3. تصنيف الفاتورة (مشتريات/مصروفات/أصول)
4. فحص أي مخالفات أو غلطات
5. أجب باللغة العربية"""
        user_message = f"حلل الفاتورة التالية:\n{json.dumps(invoice_data, ensure_ascii=False, indent=2)}"
        return self.call_ai(system_prompt, user_message)
    
    # ==========================================
    # 🏷️ تصنيف المصروفات
    # ==========================================
    
    def classify_expense(self, description, amount, supplier=None):
        accounts = frappe.get_list("Account",
            filters={"company": self.company, "root_type": "Expense", "is_group": 0},
            fields=["name", "account_name"], limit=100)
        system_prompt = f"""أنت مصنف مصروفات ذكي. حدد الحساب الأنسب.
الحسابات المتاحة: {json.dumps([a["name"] for a in accounts], ensure_ascii=False)}
أجب باللغة العربية."""
        user_message = f"صنف المصروف:\n- الوصف: {description}\n- المبلغ: {amount}\n- المورد: {supplier or 'غير محدد'}"
        return self.call_ai(system_prompt, user_message)
    
    # ==========================================
    # 📊 التقرير اليومي
    # ==========================================
    
    def generate_daily_report(self):
        today = nowdate()
        data = self._collect_daily_data(today)
        system_prompt = """أنت محلل مالي ذكي. أنشئ تقرير يومي شامل يتضمن:
1. ملخص المبيعات والمشتريات
2. تحليل المصروفات
3. تنبيهات مهمة
4. توصيات لتحسين الأداء
اكتب التقرير باللغة العربية بشكل مهني."""
        user_message = f"بيانات اليوم ({today}):\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        return self.call_ai(system_prompt, user_message)
    
    # ==========================================
    # 🔍 فحص الغلطات المحاسبية
    # ==========================================
    
    def check_accounting_errors(self):
        errors_found = []
        try:
            invoices_no_account = frappe.db.sql("""
                SELECT pi.name FROM `tabPurchase Invoice` pi
                LEFT JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
                WHERE pi.docstatus = 0 AND (pii.expense_account IS NULL OR pii.expense_account = '')
                LIMIT 10
            """, as_dict=True)
            if invoices_no_account:
                errors_found.append({"type": "missing_account", "message": f"يوجد {len(invoices_no_account)} فاتورة بدون حساب مصروفات"})
        except:
            pass
        try:
            negative_stock = frappe.db.sql("SELECT item_code FROM `tabBin` WHERE actual_qty < 0 LIMIT 10", as_dict=True)
            if negative_stock:
                errors_found.append({"type": "negative_stock", "message": f"يوجد {len(negative_stock)} صنف بكمية سالبة"})
        except:
            pass
        try:
            overdue = frappe.db.count("Sales Invoice", {"outstanding_amount": [">", 0], "due_date": ["<", nowdate()], "docstatus": 1})
            if overdue > 0:
                errors_found.append({"type": "overdue_payments", "message": f"يوجد {overdue} فاتورة متأخرة"})
        except:
            pass
        return errors_found
    
    # ==========================================
    # 🔧 أدوات مساعدة
    # ==========================================
    
    def _build_accounting_context(self):
        accounts = frappe.get_list("Account", filters={"company": self.company, "is_group": 0},
            fields=["name", "account_name", "account_type", "root_type"], limit=300)
        suppliers = frappe.get_list("Supplier", fields=["name", "supplier_name"], limit=100)
        items = frappe.get_list("Item", fields=["name", "item_name", "item_group"], limit=200)
        return {
            "accounts": [{"name": a["name"], "type": a["root_type"]} for a in accounts],
            "suppliers": [s["supplier_name"] for s in suppliers],
            "items": [{"code": i["name"], "name": i["item_name"]} for i in items],
        }
    
    def _collect_daily_data(self, date):
        company = self.company
        try:
            sales = frappe.db.sql("SELECT COUNT(*) as count, COALESCE(SUM(grand_total),0) as total FROM `tabSales Invoice` WHERE docstatus=1 AND posting_date=%s AND company=%s", (date, company), as_dict=True)[0]
        except:
            sales = {"count": 0, "total": 0}
        try:
            purchases = frappe.db.sql("SELECT COUNT(*) as count, COALESCE(SUM(grand_total),0) as total FROM `tabPurchase Invoice` WHERE docstatus=1 AND posting_date=%s AND company=%s", (date, company), as_dict=True)[0]
        except:
            purchases = {"count": 0, "total": 0}
        try:
            payments = frappe.db.sql("SELECT COUNT(*) as count, COALESCE(SUM(paid_amount),0) as total FROM `tabPayment Entry` WHERE docstatus=1 AND posting_date=%s AND company=%s", (date, company), as_dict=True)[0]
        except:
            payments = {"count": 0, "total": 0}
        return {
            "date": date,
            "total_sales": flt(sales.get("total", 0)),
            "sales_count": sales.get("count", 0),
            "total_purchases": flt(purchases.get("total", 0)),
            "purchases_count": purchases.get("count", 0),
            "total_payments": flt(payments.get("total", 0)),
            "payments_count": payments.get("count", 0),
        }