import frappe
import json
from ai_agent.agent_engine import AIAgentEngine


@frappe.whitelist()
def process_invoice(supplier, items, bill_no=None, date=None, due_date=None):
    """معالجة فاتورة مشتريات بالـ AI"""
    engine = AIAgentEngine()
    
    invoice_data = {
        "supplier": supplier,
        "items": frappe.parse_json(items) if isinstance(items, str) else items,
        "bill_no": bill_no,
        "date": date,
        "due_date": due_date,
    }
    
    return engine.process_purchase_invoice(invoice_data)


@frappe.whitelist()
def check_errors():
    """فحص الغلطات المحاسبية"""
    engine = AIAgentEngine()
    return engine.check_accounting_errors()


@frappe.whitelist()
def classify_expense(description, amount, supplier=None):
    """تصنيف مصروف"""
    engine = AIAgentEngine()
    return engine.classify_expense(description, float(amount), supplier)


@frappe.whitelist()
def generate_daily_report():
    """إنشاء تقرير يومي"""
    engine = AIAgentEngine()
    return engine.generate_daily_report()


@frappe.whitelist()
def chat(message):
    """محادثة مع الـ AI Agent"""
    engine = AIAgentEngine()
    
    system_prompt = """أنت مساعد ذكي متصل بنظام ERPNext.
تستطيع مساعدة المستخدم في:
1. أسئلة عن الحسابات والمحاسبة
2. أسئلة عن الضرائب السعودية
3. فحص النظام واكتشاف المشاكل
4. استعلامات عن البيانات
أجب باللغة العربية بشكل مهني ومفصل."""
    
    return engine.call_ai(system_prompt, message)