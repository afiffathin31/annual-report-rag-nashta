/**
 * AI Assistant Copilot & Proposal Generation Engine (Frontend)
 */

class AIAssistantUI {
  constructor() {
    this.drawer = document.getElementById('aiCopilotDrawer');
    this.chatBody = document.getElementById('copilotChatBody');
    this.input = document.getElementById('copilotInput');
    this.sendBtn = document.getElementById('copilotSendBtn');
    this.floatingTrigger = document.getElementById('floatingAiTrigger');
    this.closeBtn = document.getElementById('copilotCloseBtn');
    this.quickPrompts = document.querySelectorAll('.prompt-chip');
    
    // Proposal Modal
    this.modalBackdrop = document.getElementById('proposalModal');
    this.modalTitle = document.getElementById('proposalModalTitle');
    this.modalBody = document.getElementById('proposalModalBody');
    this.modalCloseBtn = document.getElementById('modalCloseBtn');
    this.modalCopyBtn = document.getElementById('modalCopyBtn');
    
    this.activeEmiten = 'BRIS';
    this.initEvents();
  }

  initEvents() {
    if (this.floatingTrigger) {
      this.floatingTrigger.addEventListener('click', () => this.toggleDrawer(true));
    }
    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.toggleDrawer(false));
    }
    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.sendMessage());
    }
    if (this.input) {
      this.input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') this.sendMessage();
      });
    }
    if (this.quickPrompts) {
      this.quickPrompts.forEach(chip => {
        chip.addEventListener('click', () => {
          const text = chip.getAttribute('data-prompt') || chip.innerText;
          this.input.value = text;
          this.sendMessage();
        });
      });
    }
    if (this.modalCloseBtn) {
      this.modalCloseBtn.addEventListener('click', () => this.closeProposalModal());
    }
    if (this.modalCopyBtn) {
      this.modalCopyBtn.addEventListener('click', () => this.copyProposalToClipboard());
    }
  }

  setActiveEmiten(code) {
    this.activeEmiten = code;
  }

  toggleDrawer(open) {
    if (!this.drawer) return;
    if (open) {
      this.drawer.classList.add('open');
      this.floatingTrigger.style.display = 'none';
      this.input.focus();
    } else {
      this.drawer.classList.remove('open');
      this.floatingTrigger.style.display = 'flex';
    }
  }

  async sendMessage() {
    const query = this.input.value.trim();
    if (!query) return;

    this.appendMessage(query, 'user');
    this.input.value = '';

    // Show typing bubble
    const typingId = this.appendTypingBubble();

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          emiten_code: this.activeEmiten
        })
      });
      const data = await resp.json();
      this.removeTypingBubble(typingId);

      if (data.proposal_markdown) {
        this.appendMessage(
          `📄 **Draf Proposal Penawaran 10 Pilar Berhasil Dibuat!**\n\nProposal lengkap telah disiapkan untuk **${data.emiten_code}**.\n\n[Klik Disini untuk Membuka Proposal Lengkap](#)`,
          'assistant',
          () => this.openProposalModal(data.title, data.proposal_markdown)
        );
        this.openProposalModal(data.title, data.proposal_markdown);
      } else {
        this.appendMessage(data.reply || 'Maaf, tidak ada respon.', 'assistant');
      }
    } catch (err) {
      this.removeTypingBubble(typingId);
      this.appendMessage(`⚠️ Terjadi kesalahan: ${err.message}`, 'assistant');
    }
  }

  renderMarkdown(text) {
    if (!text) return '';

    let lines = text.split('\n');
    let htmlLines = [];
    let inTable = false;
    let tableHeader = [];
    let tableRows = [];
    let inList = false;
    let listType = 'ul';

    const flushTable = () => {
      if (!inTable) return;
      let tblHtml = '<div style="overflow-x:auto;margin:1rem 0;"><table style="width:100%;border-collapse:collapse;font-size:0.85rem;background:#0d1527;border-radius:8px;overflow:hidden;border:1px solid #1e293b;">';
      if (tableHeader.length > 0) {
        tblHtml += '<thead><tr style="background:#1e293b;color:#38bdf8;text-align:left;">';
        tableHeader.forEach(th => {
          tblHtml += `<th style="padding:10px 14px;border-bottom:2px solid #334155;font-weight:600;">${th}</th>`;
        });
        tblHtml += '</tr></thead>';
      }
      tblHtml += '<tbody>';
      tableRows.forEach((row, rIdx) => {
        let bg = rIdx % 2 === 0 ? 'rgba(15,23,42,0.4)' : 'rgba(30,41,59,0.2)';
        tblHtml += `<tr style="background:${bg};border-bottom:1px solid #1e293b;transition:background 0.2s;">`;
        row.forEach(td => {
          tblHtml += `<td style="padding:9px 14px;color:#e2e8f0;">${td}</td>`;
        });
        tblHtml += '</tr>';
      });
      tblHtml += '</tbody></table></div>';
      htmlLines.push(tblHtml);
      inTable = false;
      tableHeader = [];
      tableRows = [];
    };

    const flushList = () => {
      if (!inList) return;
      htmlLines.push(`</${listType}>`);
      inList = false;
    };

    for (let i = 0; i < lines.length; i++) {
      let line = lines[i].trim();

      // Check Table Row: | a | b | c |
      if (line.startsWith('|') && line.endsWith('|')) {
        flushList();
        let cols = line.split('|').slice(1, -1).map(c => this._inlineFormat(c.trim()));
        
        // Skip separator line |---|---|
        if (cols.every(c => /^[\-:\s]+$/.test(c))) {
          continue;
        }

        if (!inTable) {
          inTable = true;
          tableHeader = cols;
        } else {
          tableRows.push(cols);
        }
        continue;
      } else {
        flushTable();
      }

      // Check Headers
      if (line.startsWith('#### ')) {
        flushList();
        htmlLines.push(`<h4 style="color:#38bdf8;font-size:0.95rem;font-weight:600;margin-top:1rem;margin-bottom:0.4rem;">${this._inlineFormat(line.substring(5))}</h4>`);
        continue;
      }
      if (line.startsWith('### ')) {
        flushList();
        htmlLines.push(`<h3 style="color:#06b6d4;font-size:1.08rem;font-weight:600;margin-top:1.2rem;margin-bottom:0.5rem;">${this._inlineFormat(line.substring(4))}</h3>`);
        continue;
      }
      if (line.startsWith('## ')) {
        flushList();
        htmlLines.push(`<h2 style="color:#38bdf8;font-size:1.25rem;font-weight:700;margin-top:1.5rem;margin-bottom:0.6rem;padding-bottom:0.4rem;border-bottom:1px solid #1e293b;">${this._inlineFormat(line.substring(3))}</h2>`);
        continue;
      }
      if (line.startsWith('# ')) {
        flushList();
        htmlLines.push(`<h1 style="color:#f8fafc;font-size:1.45rem;font-weight:800;margin-bottom:0.8rem;padding-bottom:0.5rem;border-bottom:2px solid #06b6d4;">${this._inlineFormat(line.substring(2))}</h1>`);
        continue;
      }

      // Check Horizontal Rule
      if (line === '---' || line === '***' || line === '___') {
        flushList();
        htmlLines.push('<hr style="border:none;border-top:1px solid #334155;margin:1.25rem 0;">');
        continue;
      }

      // Check Blockquote
      if (line.startsWith('> ')) {
        flushList();
        htmlLines.push(`<div style="background:rgba(15,23,42,0.7);border-left:4px solid #06b6d4;padding:0.6rem 1rem;margin:0.6rem 0;border-radius:4px;color:#94a3b8;font-style:italic;line-height:1.6;">${this._inlineFormat(line.substring(2))}</div>`);
        continue;
      }

      // Check Lists
      if (line.startsWith('- ') || line.startsWith('* ')) {
        if (!inList || listType !== 'ul') {
          flushList();
          inList = true;
          listType = 'ul';
          htmlLines.push('<ul style="margin:0.4rem 0 0.6rem 1.2rem;padding-left:0.5rem;color:#e2e8f0;line-height:1.6;">');
        }
        htmlLines.push(`<li style="margin-bottom:0.25rem;">${this._inlineFormat(line.substring(2))}</li>`);
        continue;
      }
      if (/^\d+\.\s/.test(line)) {
        let content = line.replace(/^\d+\.\s/, '');
        if (!inList || listType !== 'ol') {
          flushList();
          inList = true;
          listType = 'ol';
          htmlLines.push('<ol style="margin:0.4rem 0 0.6rem 1.2rem;padding-left:0.5rem;color:#e2e8f0;line-height:1.6;">');
        }
        htmlLines.push(`<li style="margin-bottom:0.25rem;">${this._inlineFormat(content)}</li>`);
        continue;
      }

      flushList();

      if (!line) {
        htmlLines.push('<div style="height:0.5rem;"></div>');
      } else {
        htmlLines.push(`<p style="margin:0.35rem 0;line-height:1.6;color:#cbd5e1;">${this._inlineFormat(line)}</p>`);
      }
    }

    flushTable();
    flushList();

    return htmlLines.join('\n');
  }

  _inlineFormat(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#f8fafc;font-weight:600;">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em style="color:#cbd5e1;">$1</em>')
      .replace(/`([^`]+)`/g, '<code style="background:#090d16;padding:2px 6px;border-radius:4px;color:#38bdf8;font-size:0.82rem;font-family:monospace;border:1px solid #1e293b;">$1</code>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:#06b6d4;text-decoration:underline;font-weight:500;">$1</a>');
  }

  appendMessage(text, sender, onClickAction = null) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble bubble-${sender}`;
    bubble.innerHTML = this.renderMarkdown(text);

    if (onClickAction) {
      bubble.style.cursor = 'pointer';
      bubble.addEventListener('click', onClickAction);
    }

    this.chatBody.appendChild(bubble);
    this.chatBody.scrollTop = this.chatBody.scrollHeight;
  }

  appendTypingBubble() {
    const id = 'typing_' + Date.now();
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = 'chat-bubble bubble-assistant';
    bubble.innerHTML = '<span style="color:#06b6d4;">🤖 Sedang menganalisis dokumen...</span>';
    this.chatBody.appendChild(bubble);
    this.chatBody.scrollTop = this.chatBody.scrollHeight;
    return id;
  }

  removeTypingBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  openProposalModal(title, markdownContent) {
    if (!this.modalBackdrop) return;
    this.modalTitle.innerText = title || 'Executive Proposal 10 Pilar Nashta';
    this.modalBody.innerHTML = `<div style="font-family:var(--font-sans);color:#e2e8f0;line-height:1.7;">${this.renderMarkdown(markdownContent)}</div>`;
    this.modalBackdrop.classList.add('open');
  }

  closeProposalModal() {
    if (this.modalBackdrop) {
      this.modalBackdrop.classList.remove('open');
    }
  }

  copyProposalToClipboard() {
    const text = this.modalBody.innerText;
    navigator.clipboard.writeText(text).then(() => {
      this.modalCopyBtn.innerHTML = '✅ Berhasil Disalin!';
      setTimeout(() => {
        this.modalCopyBtn.innerHTML = '📋 Salin Teks Proposal';
      }, 2000);
    });
  }
}

window.aiAssistantUI = new AIAssistantUI();

