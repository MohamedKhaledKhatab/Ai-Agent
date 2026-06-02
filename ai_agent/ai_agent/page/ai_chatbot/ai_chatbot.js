frappe.pages['ai_chatbot'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'AI Agent',
        single_column: true
    });

    $(wrapper).find('.layout-main-section').html(`
        <div class="ai-chatbot" style="max-width:800px;margin:0 auto;">
            <div class="quick-actions" style="display:flex;gap:8px;margin-bottom:15px;flex-wrap:wrap;">
                <button class="btn btn-sm btn-primary quick-cmd" data-cmd="check_system">فحص السيستم</button>
                <button class="btn btn-sm btn-warning quick-cmd" data-cmd="find_bugs">اكتشاف البقز</button>
                <button class="btn btn-sm btn-info quick-cmd" data-cmd="check_accounting">فحص IFRS</button>
                <button class="btn btn-sm btn-success quick-cmd" data-cmd="check_tax">فحص الضريبة السعودية</button>
                <button class="btn btn-sm btn-secondary quick-cmd" data-cmd="full_report">تقرير شامل</button>
            </div>
            <div id="chat-area" style="height:420px;overflow-y:auto;border:1px solid #ddd;border-radius:10px;padding:15px;background:#f8f9fa;"></div>
            <div style="display:flex;gap:10px;margin-top:10px;">
                <input type="text" id="chat-input" class="form-control" placeholder="اكتب رسالتك هنا..." style="flex:1;border-radius:20px;padding:10px 20px;" />
                <button class="btn btn-primary" id="chat-send" style="border-radius:50%;width:45px;height:45px;">
                    <i class="fa fa-paper-plane"></i>
                </button>
            </div>
        </div>
    `);

    var chat_area = $('#chat-area');

    function add_msg(role, content) {
        var bg = role === 'user' ? '#007bff' : '#ffffff';
        var color = role === 'user' ? '#fff' : '#333';
        var align = role === 'user' ? 'right' : 'left';
        var icon = role === 'user' ? '👤' : '🤖';
        var html = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        chat_area.append(`
            <div style="display:flex;margin-bottom:12px;justify-content:${align};">
                <div style="max-width:75%;padding:12px 16px;border-radius:15px;background:${bg};color:${color};box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                    <div style="font-size:11px;opacity:0.7;margin-bottom:4px;">${icon} ${role==='user'?'أنت':'AI Agent'}</div>
                    <div style="font-size:14px;line-height:1.6;text-align:right;">${html}</div>
                </div>
            </div>
        `);
        chat_area.scrollTop(chat_area[0].scrollHeight);
    }

    function add_loading() {
        var id = 'load-' + Date.now();
        chat_area.append(`
            <div id="${id}" style="display:flex;margin-bottom:12px;">
                <div style="padding:12px 16px;border-radius:15px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                    <span>⏳ جاري التحليل...</span>
                </div>
            </div>
        `);
        chat_area.scrollTop(chat_area[0].scrollHeight);
        return id;
    }

    function send_msg(message) {
        if (!message.trim()) return;
        add_msg('user', message);
        $('#chat-input').val('');
        var load_id = add_loading();
        
        frappe.call({
            method: 'ai_agent.chatbot.chat',
            args: { message: message },
            callback: function(r) {
                $('#' + load_id).remove();
                if (r.message) {
                    add_msg('bot', r.message.reply);
                }
            },
            error: function() {
                $('#' + load_id).remove();
                add_msg('bot', 'حدث خطأ، حاول مرة أخرى');
            }
        });
    }

    $('#chat-send').on('click', function() { send_msg($('#chat-input').val()); });
    $('#chat-input').on('keypress', function(e) { if(e.which===13) send_msg($(this).val()); });
    
    $('.quick-cmd').on('click', function() {
        var msgs = {
            'check_system': 'اعمل فحص شامل للسيستم',
            'find_bugs': 'اكتشف البقز والمشاكل البرمجية',
            'check_accounting': 'فحص الحسابات طبقا للمعايير الدولية IFRS',
            'check_tax': 'فحص مطابقة النظام مع الضريبة السعودية ZATCA',
            'full_report': 'تقرير شامل بكل شيء'
        };
        send_msg(msgs[$(this).data('cmd')]);
    });

    add_msg('bot', 'أهلا بك! أنا المساعد الذكي لنظام ERPNext.\n\nأقدر أساعدك في:\n- فحص السيستم واكتشاف المشاكل\n- اكتشاف البقز البرمجية\n- فحص المعايير الدولية IFRS\n- فحص الضريبة السعودية ZATCA\n- تقارير شاملة\n\nاستخدم الأزرار فوق أو اكتب طلبك!');
};
