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

  appendMessage(text, sender, onClickAction = null) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble bubble-${sender}`;
    
    // Rich Markdown formatting for Chat Copilot
    let formatted = text
      .replace(/#### (.*?)\n/g, '<h4 style="color:#38bdf8;font-size:0.88rem;margin-top:0.6rem;margin-bottom:0.3rem;">$1</h4>')
      .replace(/### (.*?)\n/g, '<h3 style="color:#06b6d4;font-size:0.95rem;margin-top:0.5rem;margin-bottom:0.4rem;">$1</h3>')
      .replace(/## (.*?)\n/g, '<h2 style="color:#38bdf8;font-size:1.05rem;margin-top:0.6rem;margin-bottom:0.4rem;">$1</h2>')
      .replace(/# (.*?)\n/g, '<h1 style="color:#f8fafc;font-size:1.15rem;margin-top:0.7rem;margin-bottom:0.5rem;">$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#f1f5f9;">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em style="color:#cbd5e1;">$1</em>')
      .replace(/`([^`]+)`/g, '<code style="background:#090d16;padding:2px 6px;border-radius:4px;color:#38bdf8;font-size:0.8rem;border:1px solid #1e293b;">$1</code>')
      .replace(/^>\s*(.*?)$/gm, '<div style="background:rgba(15,23,42,0.6);border-left:3px solid #06b6d4;padding:0.4rem 0.75rem;margin:0.4rem 0;border-radius:4px;color:#94a3b8;font-style:italic;font-size:0.8rem;">$1</div>')
      .replace(/\n/g, '<br>');

    bubble.innerHTML = formatted;

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
    bubble.innerHTML = '<span style="color:#06b6d4;">🤖 Sedang menganalisis laporan tahunan...</span>';
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
    this.modalTitle.innerText = title || 'Proposal Penawaran 10 Pilar Nashta';
    
    // Parse Markdown to HTML for rendering
    let htmlContent = markdownContent
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 style="color:#06b6d4;margin-top:1.2rem;margin-bottom:0.5rem;">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 style="color:#38bdf8;margin-bottom:0.75rem;font-size:1.4rem;">$1</h1>')
      .replace(/^\> (.*$)/gim, '<blockquote style="border-left:3px solid #06b6d4;padding-left:10px;margin:8px 0;color:#94a3b8;">$1</blockquote>')
      .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/gim, '<em>$1</em>')
      .replace(/`([^`]+)`/gim, '<code style="background:#0b0f17;padding:2px 6px;border-radius:4px;color:#34d399;">$1</code>')
      .replace(/\|(.+)\|/gim, (match) => {
        return match; // Keep tables intact
      });

    this.modalBody.innerHTML = `<div style="white-space:pre-wrap;font-family:var(--font-sans);">${markdownContent}</div>`;
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
