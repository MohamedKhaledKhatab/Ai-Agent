import frappe
import json
from frappe.utils import nowdate, flt
from ai_agent.agent_engine import AIAgentEngine


@frappe.whitelist()
def chat(message, session_id=None):
    """نقطة الدخول الرئيسية للشات بوت"""
    
    engine = AIAgentEngine()
    intent = detect_intent(message)
    
    if intent == "check_system":
        return {"reply": check_system(engine), "type": "report"}
    elif intent == "find_bugs":
        return {"reply": find_bugs(engine), "type": "report"}
    elif intent == "check_accounting":
        return {"reply": check_accounting_standards(engine), "type": "report"}
    elif intent == "check_tax":
        return {"reply": check_saudi_tax(engine), "type": "report"}
    elif intent == "full_report":
        return {"reply": full_report(engine), "type": "report"}
    else:
        reply = engine.call_ai(
            "أنت مساعد ذكي متصل بنظام ERPNext. أجب باللغة العربية.",
            message
        )
        return {"reply": reply, "type": "text"}


def detect_intent(message):
    """تحديد نية المستخدم"""
    msg = message.lower()
    
    if any(k in msg for k in ["فحص السيستم", "فحص النظام", "system check"]):
        return "check_system"
    elif any(k in msg for k in ["بقز", "بق", "bugs", "أخطاء برمجية"]):
        return "find_bugs"
    elif any(k in msg for k in ["معايير دولية", "ifrs", "محاسبة", "فحص الحسابات"]):
        return "check_accounting"
    elif any(k in msg for k in ["ضريبة", "zatca", "vat", "الضريبة السعودية"]):
        return "check_tax"
    elif any(k in msg for k in ["تقرير شامل", "كل شيء", "full report"]):
        return "full_report"
    
    return "free_chat"


# ==========================================
# 🔍 فحص السيستم
# ==========================================

def check_system(engine):
    """فحص شامل للسيستم"""
    
    report = "**🔍 تقرير فحص السيستم**\n\n"
    issues_count = 0
    
    # 1. فحص المستندات المعلقة
    pending_pi = frappe.db.count("Purchase Invoice", {"docstatus": 0})
    pending_si = frappe.db.count("Sales Invoice", {"docstatus": 0})
    pending_jv = frappe.db.count("Journal Entry", {"docstatus": 0})
    
    report += "**📄 المستندات المعلقة:**\n"
    if pending_pi > 0:
        report += f"  • ⚠️ {pending_pi} فاتورة مشتريات معلقة\n"
        issues_count += 1
    if pending_si > 0:
        report += f"  • ⚠️ {pending_si} فاتورة مبيعات معلقة\n"
        issues_count += 1
    if pending_jv > 0:
        report += f"  • ⚠️ {pending_jv} قيد يومي غير معتمد\n"
        issues_count += 1
    if pending_pi == 0 and pending_si == 0 and pending_jv == 0:
        report += "  • ✅ لا توجد مستندات معلقة\n"
    
    # 2. فحص أوامر التسليم المتأخرة
    overdue = frappe.db.count("Sales Order", {
        "docstatus": 1, "status": "To Deliver",
        "delivery_date": ["<", nowdate()]
    })
    report += "\n**🚚 أوامر التسليم:**\n"
    if overdue > 0:
        report += f"  • ❌ {overdue} أمر تسليم متأخر\n"
        issues_count += 1
    else:
        report += "  • ✅ لا توجد أوامر متأخرة\n"
    
    # 3. فحص المستخدمين بدون أدوار
    users_no_role = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabUser` u
        LEFT JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1 AND hr.name IS NULL 
        AND u.name NOT IN ('Guest', 'Administrator')
    """, as_dict=True)[0]["cnt"]
    
    report += "\n**🔐 الصلاحيات:**\n"
    if users_no_role > 0:
        report += f"  • ⚠️ {users_no_role} مستخدم بدون أدوار\n"
        issues_count += 1
    else:
        report += "  • ✅ جميع المستخدمين لديهم أدوار\n"
    
    # 4. فحص Error Logs
    recent_errors = frappe.db.count("Error Log", {
        "creation": [">=", frappe.utils.add_days(nowdate(), -1)]
    })
    report += "\n**🐛 الأخطاء (آخر 24 ساعة):**\n"
    if recent_errors > 0:
        report += f"  • ❌ {recent_errors} خطأ في آخر 24 ساعة\n"
        issues_count += 1
    else:
        report += "  • ✅ لا توجد أخطاء\n"
    
    # 5. فحص Scheduler
    report += "\n**⏰ Scheduler:**\n"
    try:
        scheduler_status = frappe.utils.scheduler.get_scheduler_status()
        if scheduler_status == "active":
            report += "  • ✅ Scheduler شغال\n"
        else:
            report += f"  • ❌ Scheduler مش شغال: {scheduler_status}\n"
            issues_count += 1
    except:
        report += "  • ⚠️ لم أستطع التحقق\n"
    
    # الخلاصة
    report += f"\n**📊 الخلاصة:** "
    if issues_count == 0:
        report += "✅ السيستم شغال تمام!"
    else:
        report += f"❌ في {issues_count} مشكلة محتاجة انتباه"
    
    # تحليل AI
    ai_analysis = engine.call_ai(
        "أنت خبير أنظمة ERPNext. حلل نتائج الفحص التالية وقدم توصيات.",
        report
    )
    report += f"\n\n**🤖 تحليل AI:**\n{ai_analysis}"
    
    return report


# ==========================================
# 🐛 اكتشاف البقز
# ==========================================

def find_bugs(engine):
    """اكتشاف البقز والمشاكل البرمجية"""
    
    report = "**🐛 تقرير اكتشاف البقز**\n\n"
    bugs = []
    
    # 1. Error Logs الأخيرة
    error_logs = frappe.get_list("Error Log",
        filters={"creation": [">=", frappe.utils.add_days(nowdate(), -7)]},
        fields=["error", "method", "creation"],
        order_by="creation desc",
        limit=30
    )
    
    if error_logs:
        report += f"**🔴 Error Logs (آخر 7 أيام): {len(error_logs)} خطأ**\n"
        
        # تجميع حسب النوع
        error_types = {}
        for log in error_logs:
            error_key = str(log.get("error", ""))[:80]
            if error_key not in error_types:
                error_types[error_key] = 0
            error_types[error_key] += 1
        
        for err, count in sorted(error_types.items(), key=lambda x: -x[1])[:5]:
            report += f"  • ({count}x) {err}\n"
        bugs.append("errors")
    else:
        report += "**🔴 Error Logs:** ✅ لا توجد أخطاء\n"
    
    # 2. مخزون سالب
    negative_stock = frappe.db.sql("""
        SELECT item_code, warehouse, actual_qty 
        FROM `tabBin` WHERE actual_qty < 0 LIMIT 10
    """, as_dict=True)
    
    report += f"\n**📦 مخزون سالب:**\n"
    if negative_stock:
        report += f"  • ❌ يوجد {len(negative_stock)} صنف بكمية سالبة\n"
        for s in negative_stock[:3]:
            report += f"    - {s['item_code']} في {s['warehouse']}: {s['actual_qty']}\n"
        bugs.append("negative_stock")
    else:
        report += "  • ✅ لا يوجد مخزون سالب\n"
    
    # 3. فواتير بمبالغ سالبة
    negative_invoices = frappe.db.sql("""
        SELECT name, supplier, grand_total 
        FROM `tabPurchase Invoice` 
        WHERE docstatus = 1 AND grand_total < 0 LIMIT 10
    """, as_dict=True)
    
    report += f"\n**💰 فواتير بمبالغ سالبة:**\n"
    if negative_invoices:
        report += f"  • ❌ يوجد {len(negative_invoices)} فاتورة بمبلغ سالب\n"
        bugs.append("negative_invoices")
    else:
        report += "  • ✅ لا توجد فواتير بمبالغ سالبة\n"
    
    # 4. Custom Fields يتيمة
    orphan_fields = frappe.db.sql("""
        SELECT cf.name, cf.dt, cf.fieldname
        FROM `tabCustom Field` cf
        WHERE cf.dt NOT IN (SELECT name FROM `tabDocType`)
        LIMIT 10
    """, as_dict=True)
    
    report += f"\n**🔧 Custom Fields يتيمة:**\n"
    if orphan_fields:
        report += f"  • ⚠️ يوجد {len(orphan_fields)} حقل لـ DocType محذوف\n"
        bugs.append("orphan_fields")
    else:
        report += "  • ✅ لا توجد حقول يتيمة\n"
    
    # الخلاصة
    if not bugs:
        report += "\n✅ **مفيش بقز مكتشفة! النظام شغال نظيف.**"
    else:
        report += f"\n🚨 **في {len(bugs)} نوع من المشاكل مكتشف**"
    
    # تحليل AI
    ai_analysis = engine.call_ai(
        "أنت خبير debugging. حلل الأخطاء التالية وقدم حلول.",
        report
    )
    report += f"\n\n**🤖 تحليل AI:**\n{ai_analysis}"
    
    return report


# ==========================================
# 📊 فحص المعايير الدولية IFRS
# ==========================================

def check_accounting_standards(engine):
    """فحص مطابقة الحسابات مع IFRS"""
    
    report = "**📊 تقرير فحص المعايير الدولية (IFRS)**\n\n"
    violations = []
    
    # IAS 2 - المخزون
    negative_stock = frappe.db.sql("""
        SELECT item_code, warehouse, actual_qty 
        FROM `tabBin` WHERE actual_qty < 0 LIMIT 10
    """, as_dict=True)
    
    report += "**📌 IAS 2 - المخزون:**\n"
    if negative_stock:
        report += f"  • 🔴 يوجد {len(negative_stock)} صنف بكمية سالبة (مخالفة)\n"
        report += "    الحل: تصحيح الكميات السالبة فوراً\n"
        violations.append("IAS2")
    else:
        report += "  • ✅ مطابق\n"
    
    # IAS 16 - الأصول الثابتة
    assets_no_depreciation = frappe.db.sql("""
        SELECT name, asset_name, gross_purchase_amount
        FROM `tabAsset`
        WHERE docstatus = 1 AND calculate_depreciation = 0
        AND gross_purchase_amount > 1000
        LIMIT 10
    """, as_dict=True)
    
    report += "\n**📌 IAS 16 - الأصول الثابتة:**\n"
    if assets_no_depreciation:
        report += f"  • 🔴 يوجد {len(assets_no_depreciation)} أصل بدون إهلاك\n"
        report += "    الحل: تفعيل الإهلاك وتحديد العمر الإنتاجي\n"
        violations.append("IAS16")
    else:
        report += "  • ✅ مطابق\n"
    
    # IFRS 9 - الأدوات المالية
    old_receivables = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabSales Invoice`
        WHERE docstatus = 1 AND outstanding_amount > 0
        AND due_date < %s
    """, (frappe.utils.add_months(nowdate(), -6),), as_dict=True)[0]["cnt"]
    
    report += "\n**📌 IFRS 9 - الأدوات المالية:**\n"
    if old_receivables > 0:
        report += f"  • 🔴 {old_receivables} عميل بمبالغ مستحقة أقدم من 6 أشهر\n"
        report += "    الحل: حساب مخصص خسائر ائتمانية (ECL)\n"
        violations.append("IFRS9")
    else:
        report += "  • ✅ مطابق\n"
    
    # IAS 1 - عرض القوائم المالية
    report += "\n**📌 IAS 1 - عرض القوائم المالية:**\n"
    equity_accounts = frappe.db.count("Account", {
        "company": engine.company, "root_type": "Equity", "is_group": 0
    })
    if equity_accounts < 2:
        report += f"  • 🟡 عدد حسابات حقوق الملكية قليل ({equity_accounts})\n"
        report += "    الحل: إضافة حسابات: رأس المال، الأرباح المحتجزة، الاحتياطي\n"
        violations.append("IAS1")
    else:
        report += "  • ✅ مطابق\n"
    
    # الخلاصة
    if not violations:
        report += "\n✅ **الحسابات مطابقة للمعايير الدولية!**"
    else:
        report += f"\n🚨 **في {len(violations)} مخالفة للمعايير الدولية**"
    
    # تحليل AI
    ai_analysis = engine.call_ai(
        "أنت خبير محاسبة دولية IFRS. حلل المخالفات التالية وقدم حلول تفصيلية.",
        report
    )
    report += f"\n\n**🤖 تحليل AI المفصل:**\n{ai_analysis}"
    
    return report


# ==========================================
# 🇸🇦 فحص الضريبة السعودية
# ==========================================

def check_saudi_tax(engine):
    """فحص مطابقة الضريبة السعودية"""
    
    report = "**🇸🇦 تقرير فحص الضريبة السعودية (ZATCA/VAT)**\n\n"
    violations = []
    
    # 1. إعدادات الضريبة
    report += "**📌 إعدادات الضريبة:**\n"
    
    vat_accounts = frappe.get_list("Account", {
        "company": engine.company,
        "account_type": "Tax",
    })
    
    if not vat_accounts:
        report += "  • 🔴 لم يتم إعداد حساب ضريبة القيمة المضافة\n"
        report += "    غرامة محتملة: تصل إلى 50% من قيمة الضريبة\n"
        violations.append("vat_account")
    else:
        report += "  • ✅ حساب الضريبة موجود\n"
    
    # 2. قوالب الضريبة
    tax_templates = frappe.get_list("Sales Taxes and Charges Template", {
        "company": engine.company
    })
    
    report += "\n**📌 قوالب الضريبة:**\n"
    if not tax_templates:
        report += "  • 🔴 لم يتم إنشاء قالب ضريبة المبيعات\n"
        report += "    غرامة: 100% من قيمة الضريبة غير المحصلة\n"
        violations.append("tax_template")
    else:
        report += f"  • ✅ يوجد {len(tax_templates)} قالب ضريبي\n"
        
        # فحص نسبة الضريبة
        for t in tax_templates:
            rates = frappe.get_list("Sales Taxes and Charges", {
                "parent": t.name
            }, fields=["rate"])
            for r in rates:
                if flt(r.rate) != 15:
                    report += f"  • 🔴 نسبة الضريبة {r.rate}% بدل 15%\n"
                    violations.append("vat_rate")
    
    # 3. الرقم الضريبي للشركة
    company_tax_id = frappe.db.get_value("Company", engine.company, "tax_id")
    report += "\n**📌 الرقم الضريبي:**\n"
    if not company_tax_id:
        report += "  • 🔴 لم يتم إدخال الرقم الضريبي (TRN) للشركة\n"
        report += "    غرامة: 10,000 - 50,000 ريال\n"
        violations.append("tax_id")
    else:
        report += f"  • ✅ الرقم الضريبي: {company_tax_id}\n"
    
    # 4. فواتير بدون ضريبة
    invoices_no_tax = frappe.db.sql("""
        SELECT COUNT(*) as cnt
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Taxes and Charges` stc ON stc.parent = si.name
        WHERE si.docstatus = 1
        AND si.posting_date >= %s
        AND stc.name IS NULL
        AND si.grand_total > 0
    """, (frappe.utils.add_months(nowdate(), -3),), as_dict=True)[0]["cnt"]
    
    report += "\n**📌 فواتير بدون ضريبة (آخر 3 أشهر):**\n"
    if invoices_no_tax > 0:
        report += f"  • 🔴 يوجد {invoices_no_tax} فاتورة بدون ضريبة\n"
        report += f"    غرامة محتملة: {invoices_no_tax * 10000:,} ريال\n"
        violations.append("invoices_no_tax")
    else:
        report += "  • ✅ جميع الفواتير عليها ضريبة\n"
    
    # 5. عملاء بدون رقم ضريبي (B2B)
    b2b_no_taxid = frappe.db.sql("""
        SELECT COUNT(*) as cnt
        FROM `tabSales Invoice` si
        LEFT JOIN `tabCustomer` c ON c.name = si.customer
        WHERE si.docstatus = 1 AND si.grand_total >= 1000
        AND si.posting_date >= %s
        AND (c.tax_id IS NULL OR c.tax_id = '')
    """, (frappe.utils.add_months(nowdate(), -3),), as_dict=True)[0]["cnt"]
    
    report += "\n**📌 فواتير B2B بدون رقم ضريبي العميل:**\n"
    if b2b_no_taxid > 0:
        report += f"  • 🔴 يوجد {b2b_no_taxid} فاتورة B2B فوق 1000 ريال بدون TRN\n"
        violations.append("b2b_no_trn")
    else:
        report += "  • ✅ جميع فواتير B2B عليها أرقام ضريبية\n"
    
    # الخلاصة
    if not violations:
        report += "\n✅ **النظام مطابق لمتطلبات الضريبة السعودية!**"
    else:
        report += f"\n🚨 **في {len(violations)} مخالفة ضريبية محتاجة تصحيح عاجل**"
    
    # تحليل AI
    ai_analysis = engine.call_ai(
        """أنت خبير ضرائب سعودي متخصص في ZATCA.
حلل المخالفات التالية وحدد:
1. مرجع المخالفة من لوائح ZATCA
2. الغرامة المحتملة
3. خطوات التصحيح
4. هل تتطلب إشعار ZATCA؟""",
        report
    )
    report += f"\n\n**🤖 تحليل الخبير الضريبي AI:**\n{ai_analysis}"
    
    return report


# ==========================================
# 📋 تقرير شامل
# ==========================================

def full_report(engine):
    """تقرير شامل يجمع كل شيء"""
    
    report = "**📋 التقرير الشامل الكامل**\n"
    report += "━" * 30 + "\n\n"
    
    report += check_system(engine) + "\n\n"
    report += "━" * 30 + "\n\n"
    report += find_bugs(engine) + "\n\n"
    report += "━" * 30 + "\n\n"
    report += check_accounting_standards(engine) + "\n\n"
    report += "━" * 30 + "\n\n"
    report += check_saudi_tax(engine)
    
    return report