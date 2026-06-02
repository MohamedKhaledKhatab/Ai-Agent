import frappe
from frappe.utils import nowdate


def daily_tasks():
    """مهام يومية اتوماتيكية"""
    try:
        settings = frappe.get_single("AI Agent Settings")
        if settings.daily_report_enabled and settings.report_recipients:
            from ai_agent.ai_agent.agent_engine import AIAgentEngine
            engine = AIAgentEngine()
            report = engine.generate_daily_report()
            
            frappe.sendmail(
                recipients=settings.report_recipients.split("\n"),
                subject=f"التقرير اليومي الذكي - {nowdate()}",
                message=report,
                now=True
            )
    except Exception as e:
        frappe.log_error(f"AI Agent Daily Task Error: {str(e)}")


def check_accounting_health():
    """فحص صحة الحسابات كل ساعة"""
    try:
        settings = frappe.get_single("AI Agent Settings")
        if settings.alert_on_errors:
            from ai_agent.ai_agent.agent_engine import AIAgentEngine
            engine = AIAgentEngine()
            errors = engine.check_accounting_errors()
            
            if errors:
                for user in frappe.get_list("User", 
                    filters={"role": "Accounts Manager"}, 
                    fields=["name"]):
                    
                    notification = frappe.get_doc({
                        "doctype": "Notification Log",
                        "subject": "تنبيه: أخطاء محاسبية مكتشفة",
                        "for_user": user["name"],
                        "document_type": "Purchase Invoice",
                        "email_content": str(errors),
                    })
                    notification.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"AI Agent Health Check Error: {str(e)}")