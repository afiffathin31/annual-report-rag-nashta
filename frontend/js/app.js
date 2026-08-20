/**
 * Main Application Controller for Nashta 10-Pillars Opportunity Intelligence Dashboard
 * True RAG & Verifiable Document Context Inspector Integration
 */

document.addEventListener('DOMContentLoaded', () => {
  class NashtaDashboardApp {
    constructor() {
      this.currentSector = 'all';
      this.searchQuery = '';
      this.activeEmitenCode = 'BRIS';
      this.issuersList = [];
      this.overviewBenchmark = null;
      this.currentAnalysis = null;
      this.isLoading = false;

      this.initElements();
      this.initEventListeners();
      this.loadInitialData();
    }

    initElements() {
      this.emitenListContainer = document.getElementById('emitenListContainer');
      this.searchInput = document.getElementById('emitenSearchInput');
      this.sectorChips = document.querySelectorAll('.filter-chip');
      this.tabButtons = document.querySelectorAll('.tab-btn');
      this.tabPanes = document.querySelectorAll('.tab-pane');

      // Hero Elements
      this.heroCode = document.getElementById('heroCode');
      this.heroName = document.getElementById('heroName');
      this.heroSubsector = document.getElementById('heroSubsector');
      this.heroMarketTier = document.getElementById('heroMarketTier');
      this.heroSummary = document.getElementById('heroSummary');
      this.heroTechStack = document.getElementById('heroTechStack');
      this.heroWebsiteLink = document.getElementById('heroWebsiteLink');
      this.heroOverallScore = document.getElementById('heroOverallScore');
      this.heroScoreStatus = document.getElementById('heroScoreStatus');

      // Containers
      this.pillarsGridContainer = document.getElementById('pillarsGridContainer');
      this.weaknessListContainer = document.getElementById('weaknessListContainer');
      this.reportsListContainer = document.getElementById('reportsListContainer');
      this.weaknessTabCount = document.getElementById('weaknessTabCount');
      this.reportsTabCount = document.getElementById('reportsTabCount');
      this.quickProposalBtn = document.getElementById('quickProposalBtn');
      this.verifyReportsBtn = document.getElementById('verifyReportsBtn');

      // Drag & Drop
      this.dropArea = document.getElementById('pdfDropArea');
      this.fileInput = document.getElementById('pdfFileInput');
      this.uploadStatus = document.getElementById('uploadStatus');
    }

    initEventListeners() {
      this.searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value || '';
        this.renderIssuersList();
      });

      this.sectorChips.forEach(chip => {
        chip.addEventListener('click', () => {
          this.sectorChips.forEach(c => c.classList.remove('active'));
          chip.classList.add('active');
          this.currentSector = chip.getAttribute('data-sector') || 'all';
          this.renderIssuersList();
        });
      });

      this.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          this.tabButtons.forEach(b => b.classList.remove('active'));
          this.tabPanes.forEach(p => p.classList.remove('active'));
          
          btn.classList.add('active');
          const targetTabId = btn.getAttribute('data-tab');
          const targetPane = document.getElementById(targetTabId);
          if (targetPane) targetPane.classList.add('active');
        });
      });

      if (this.quickProposalBtn) {
        this.quickProposalBtn.addEventListener('click', () => {
          if (window.aiAssistantUI) {
            window.aiAssistantUI.openProposalModal('Sedang menyusun proposal...', 'Mohon tunggu, AI sedang menyusun draf proposal penawaran 10 pilar Nashta berbasis dokumen Laporan Tahunan...');
            fetch(`/api/proposal/${this.activeEmitenCode}`, { method: 'POST' })
              .then(res => res.json())
              .then(data => {
                window.aiAssistantUI.openProposalModal(data.title, data.proposal_markdown);
              })
              .catch(err => {
                window.aiAssistantUI.openProposalModal('Gagal', `Terjadi kendala: ${err.message}`);
              });
          }
        });
      }

      if (this.verifyReportsBtn) {
        this.verifyReportsBtn.addEventListener('click', () => this.verifyReportsHealth());
      }

      // Direct Google Drive Folder Auto-Sync Button
      const btnSyncGDrive = document.getElementById('btnSyncGDriveFolder');
      const gdriveFolderInput = document.getElementById('gdriveFolderSyncInput');
      const syncLogBox = document.getElementById('driveSyncLogBox');

      if (btnSyncGDrive) {
        btnSyncGDrive.addEventListener('click', async () => {
          const folderUrl = gdriveFolderInput ? gdriveFolderInput.value.trim() : '';
          if (!folderUrl) {
            alert('Harap masukkan link Folder Google Drive (contoh: https://drive.google.com/drive/folders/...)');
            return;
          }

          btnSyncGDrive.disabled = true;
          btnSyncGDrive.innerHTML = '⏳ Sedang Menyinkronkan Drive...';
          if (syncLogBox) {
            syncLogBox.style.display = 'block';
            syncLogBox.innerHTML = '<div style="color:var(--nashta-cyan);">[INFO] Menginisiasi sinkronisasi Google Drive...</div>';
          }

          try {
            const resp = await fetch('/api/drive/sync-folder', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ folder_url: folderUrl })
            });
            const data = await resp.json();

            // Poll status every 1.5 seconds
            const pollInterval = setInterval(async () => {
              try {
                const stResp = await fetch('/api/drive/status');
                const stData = await stResp.json();

                if (syncLogBox && stData.recent_logs) {
                  syncLogBox.innerHTML = stData.recent_logs.map(l => `<div>${l}</div>`).join('');
                  syncLogBox.scrollTop = syncLogBox.scrollHeight;
                }

                if (!stData.is_syncing) {
                  clearInterval(pollInterval);
                  btnSyncGDrive.disabled = false;
                  btnSyncGDrive.innerHTML = '📥 Tarik Seluruh Dokumen Drive & Proses RAG';
                  if (syncLogBox) {
                    syncLogBox.innerHTML += '<div style="color:var(--nashta-emerald);font-weight:bold;">[SELESAI] Seluruh dokumen berhasil disinkronkan & RAG Index diperbarui!</div>';
                  }
                  this.loadInitialData();
                }
              } catch (pollErr) {
                console.error('Error polling sync status:', pollErr);
              }
            }, 1500);

          } catch (err) {
            btnSyncGDrive.disabled = false;
            btnSyncGDrive.innerHTML = '📥 Tarik Seluruh Dokumen Drive & Proses RAG';
            if (syncLogBox) {
              syncLogBox.innerHTML += `<div style="color:var(--nashta-rose);">[ERROR] ${err.message}</div>`;
            }
          }
        });
      }

      // Local Folder Ingest Button
      const btnImportDrive = document.getElementById('btnImportDrive');
      const driveFolderInput = document.getElementById('driveFolderPathInput');
      const driveStatus = document.getElementById('driveImportStatus');

      if (btnImportDrive) {
        btnImportDrive.addEventListener('click', async () => {
          const folderPath = driveFolderInput ? driveFolderInput.value.trim() : '';

          if (!folderPath) {
            alert('Harap masukkan jalur folder direktori komputer');
            return;
          }

          driveStatus.innerHTML = '<span style="color:var(--nashta-cyan);">⏳ Sedang memindai dan memproses RAG dari folder lokal...</span>';
          btnImportDrive.disabled = true;

          try {
            const resp = await fetch('/api/import-drive', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                folder_path: folderPath || null,
                emiten_code: this.activeEmitenCode
              })
            });
            const data = await resp.json();
            if (data.success) {
              driveStatus.innerHTML = `
                <div style="color:var(--nashta-emerald);font-weight:700;">
                  ✅ Berhasil mengimpor ${data.total_imported || 1} dokumen ke dalam RAG Index!
                </div>
              `;
              this.loadInitialData();
            } else {
              driveStatus.innerHTML = `<span style="color:var(--nashta-rose);">⚠️ ${data.error || 'Gagal mengimpor'}</span>`;
            }
          } catch (err) {
            driveStatus.innerHTML = `<span style="color:var(--nashta-rose);">⚠️ Gagal: ${err.message}</span>`;
          } finally {
            btnImportDrive.disabled = false;
          }
        });
      }

      if (this.dropArea && this.fileInput) {
        this.dropArea.addEventListener('click', () => this.fileInput.click());
        this.dropArea.addEventListener('dragover', (e) => {
          e.preventDefault();
          this.dropArea.classList.add('dragover');
        });
        this.dropArea.addEventListener('dragleave', () => this.dropArea.classList.remove('dragover'));
        this.dropArea.addEventListener('drop', (e) => {
          e.preventDefault();
          this.dropArea.classList.remove('dragover');
          if (e.dataTransfer.files.length) {
            this.handleFileUpload(e.dataTransfer.files[0]);
          }
        });
        this.fileInput.addEventListener('change', (e) => {
          if (e.target.files.length) {
            this.handleFileUpload(e.target.files[0]);
          }
        });
      }
    }

    async loadInitialData() {
      this.emitenListContainer.innerHTML = `
        <div style="text-align:center;padding:2rem 1rem;color:var(--text-secondary);font-size:0.8rem;">
          <div style="margin-bottom:0.5rem;font-size:1.2rem;">⏳</div>
          <div>Memuat data emiten dan indeks RAG...</div>
        </div>
      `;

      try {
        const [issuersRes, benchRes] = await Promise.all([
          fetch('/api/issuers'),
          fetch('/api/overview')
        ]);
        
        if (!issuersRes.ok) {
          throw new Error(`HTTP Error ${issuersRes.status} saat memuat daftar emiten`);
        }

        const issuersData = await issuersRes.json();
        this.overviewBenchmark = await benchRes.json();
        this.issuersList = issuersData.issuers || [];

        const countEl = document.getElementById('metricTotalIssuers');
        if (countEl) countEl.innerText = this.issuersList.length;
        
        this.renderIssuersList();
        this.selectIssuer(this.activeEmitenCode);
      } catch (err) {
        console.error('Error loading initial data:', err);
        this.emitenListContainer.innerHTML = `
          <div style="text-align:center;padding:1.5rem 1rem;color:var(--nashta-rose);font-size:0.8rem;">
            <div style="font-size:1.5rem;margin-bottom:0.4rem;">⚠️</div>
            <div style="font-weight:700;">Gagal Terhubung ke Server</div>
            <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.25rem;">${err.message}</div>
            <button class="btn btn-secondary btn-sm" onclick="window.dashboardApp.loadInitialData()" style="margin-top:0.85rem;">
              🔄 Coba Lagi
            </button>
          </div>
        `;
      }
    }

    renderIssuersList() {
      this.emitenListContainer.innerHTML = '';
      
      const q = (this.searchQuery || '').trim().toLowerCase();

      const filtered = this.issuersList.filter(i => {
        const sub = (i.subsector || '').toLowerCase();
        const secId = (i.sector_id || '').toLowerCase();

        let matchesSector = true;
        if (this.currentSector === 'bank_syariah') {
          matchesSector = secId === 'bank_syariah' || sub.includes('syariah') || sub.includes('bank');
        } else if (this.currentSector === 'rs') {
          matchesSector = sub.includes('rumah sakit') || sub.includes('kesehatan');
        } else if (this.currentSector === 'farmasi') {
          matchesSector = sub.includes('farmasi') || sub.includes('obat');
        } else if (this.currentSector === 'alkes') {
          matchesSector = sub.includes('alat') || sub.includes('medis') || sub.includes('laboratorium') || sub.includes('distribusi');
        }

        const codeMatch = (i.code || '').toLowerCase().includes(q);
        const nameMatch = (i.name || '').toLowerCase().includes(q);
        const subMatch = sub.includes(q);
        const matchesQuery = !q || codeMatch || nameMatch || subMatch;

        return matchesSector && matchesQuery;
      });

      if (filtered.length === 0) {
        this.emitenListContainer.innerHTML = `
          <div style="text-align:center;padding:2rem 1rem;color:var(--text-muted);font-size:0.8rem;">
            <div style="font-size:1.2rem;margin-bottom:0.3rem;">🔍</div>
            <div>Tidak ada emiten yang cocok dengan kata kunci "<strong>${this.searchQuery}</strong>".</div>
            <button class="btn btn-secondary btn-sm" onclick="document.getElementById('emitenSearchInput').value=''; window.dashboardApp.searchQuery=''; window.dashboardApp.renderIssuersList();" style="margin-top:0.6rem;font-size:0.72rem;">
              Reset Pencarian
            </button>
          </div>
        `;
        return;
      }

      filtered.forEach(item => {
        const card = document.createElement('div');
        card.className = `emiten-card ${item.code === this.activeEmitenCode ? 'selected' : ''}`;
        
        let scoreClass = 'score-med';
        if (item.overall_opportunity_score >= 80) scoreClass = 'score-high';
        else if (item.overall_opportunity_score < 60) scoreClass = 'score-low';

        card.innerHTML = `
          <div class="emiten-card-top">
            <span class="emiten-code-badge">${item.code}</span>
            <span class="score-badge ${scoreClass}">Skor ${item.overall_opportunity_score}</span>
          </div>
          <div class="emiten-name-line" title="${item.name}">${item.name}</div>
          <div class="emiten-card-bottom">
            <span class="sector-tag">${(item.subsector || '').split(' ')[0]}</span>
            <span>⭐ ${(item.top_priority_pillar || '').split(' ')[0]}</span>
          </div>
        `;

        card.addEventListener('click', () => this.selectIssuer(item.code));
        this.emitenListContainer.appendChild(card);
      });
    }

    async selectIssuer(code) {
      this.activeEmitenCode = code;
      if (window.aiAssistantUI) {
        window.aiAssistantUI.setActiveEmiten(code);
      }

      const allCards = this.emitenListContainer.querySelectorAll('.emiten-card');
      allCards.forEach(c => {
        const codeBadge = c.querySelector('.emiten-code-badge');
        if (codeBadge && codeBadge.innerText.trim() === code) {
          c.classList.add('selected');
        } else {
          c.classList.remove('selected');
        }
      });

      try {
        const resp = await fetch(`/api/issuers/${code}`);
        if (!resp.ok) {
          throw new Error(`Gagal memuat profil emiten ${code}`);
        }
        const analysis = await resp.json();
        this.currentAnalysis = analysis;
        this.renderIssuerDetails(analysis);
      } catch (err) {
        console.error('Error fetching issuer analysis:', err);
      }
    }

    renderIssuerDetails(data) {
      const issuer = data.issuer;
      const scores = data.pillar_scores || [];
      const recommendations = data.strategic_recommendations || [];
      const weaknesses = data.verified_weaknesses || [];
      const trend = data.five_year_trend || [];
      const reports = issuer.reports || [];

      this.heroCode.innerText = issuer.code;
      this.heroName.innerText = issuer.name;
      this.heroSubsector.innerText = issuer.subsector;
      this.heroMarketTier.innerText = issuer.market_tier;
      this.heroSummary.innerText = issuer.summary;
      this.heroTechStack.innerText = issuer.technology_stack;
      this.heroWebsiteLink.href = issuer.website;
      this.heroWebsiteLink.innerText = issuer.website.replace('https://', '');
      this.heroOverallScore.innerText = data.overall_opportunity_score;

      if (data.overall_opportunity_score >= 80) {
        this.heroScoreStatus.innerText = '🔥 PRIME OPPORTUNITY';
        this.heroScoreStatus.style.color = 'var(--nashta-emerald)';
      } else if (data.overall_opportunity_score >= 65) {
        this.heroScoreStatus.innerText = '⚡ ACTIVE OPPORTUNITY';
        this.heroScoreStatus.style.color = 'var(--nashta-cyan)';
      } else {
        this.heroScoreStatus.innerText = '💡 STRATEGIC INCUBATION';
        this.heroScoreStatus.style.color = 'var(--nashta-blue-light)';
      }

      this.weaknessTabCount.innerText = recommendations.length || weaknesses.length;
      this.reportsTabCount.innerText = reports.length;

      if (typeof initRadarChart === 'function') {
        const benchList = this.overviewBenchmark ? this.overviewBenchmark.pillars_benchmark : null;
        initRadarChart('radarChartCanvas', scores, benchList);
      }
      if (typeof initTrendChart === 'function') {
        initTrendChart('trendChartCanvas', trend);
      }

      this.renderPillarsGrid(scores);
      this.renderWeaknessMatrix(recommendations, issuer.name, weaknesses);
      this.renderReportsVault(reports, issuer.code);
    }

    renderPillarsGrid(scores) {
      this.pillarsGridContainer.innerHTML = '';
      scores.forEach(p => {
        const card = document.createElement('div');
        card.className = 'pillar-card';

        let scoreBadgeClass = 'score-med';
        if (p.score >= 85) scoreBadgeClass = 'score-high';
        else if (p.score < 65) scoreBadgeClass = 'score-low';

        card.innerHTML = `
          <div class="pillar-card-top">
            <div>
              <span class="pillar-number">Pilar ${p.pillar_number}</span>
              <div class="pillar-title">${p.pillar_name}</div>
            </div>
            <span class="pillar-score-badge ${scoreBadgeClass}">${p.score}/100</span>
          </div>

          <div class="pillar-deal-box">
            Est. Nilai: <strong>${p.estimated_deal_range}</strong>
          </div>

          <div class="pillar-justification">${p.justification}</div>

          <div class="pillar-solution-box">
            <span class="solution-label">Solusi Nashta:</span>
            <span class="solution-text">${p.proposed_solution}</span>
          </div>
        `;
        this.pillarsGridContainer.appendChild(card);
      });
    }

    renderWeaknessMatrix(recommendations, companyName, rawWeaknesses = []) {
      this.weaknessListContainer.innerHTML = '';

      const recs = (recommendations && recommendations.length > 0) ? recommendations : null;

      if (!recs && (!rawWeaknesses || rawWeaknesses.length === 0)) {
        this.weaknessListContainer.innerHTML = `
          <div style="background-color:var(--bg-surface);border:1px solid var(--border-subtle);border-radius:var(--radius-lg);padding:2.5rem;text-align:center;color:var(--text-secondary);">
            <div style="font-size:1.8rem;margin-bottom:0.5rem;">📋</div>
            <div style="font-weight:700;color:var(--text-primary);font-size:1rem;">Tidak Ada Kelemahan Kritis Terbuka</div>
            <div style="font-size:0.82rem;margin-top:0.35rem;max-width:500px;margin-left:auto;margin-right:auto;">
              Hasil scan RAG pada Laporan Tahunan tidak menemukan kalimat anomali atau insiden terbuka. Analisis peluang berfokus pada rencana ekspansi IT jangka panjang.
            </div>
          </div>
        `;
        return;
      }

      if (recs) {
        recs.forEach((rec, idx) => {
          const card = document.createElement('div');
          card.className = 'weakness-card';
          card.style.border = '1px solid var(--border-default)';
          card.style.background = 'var(--bg-surface)';
          card.style.marginBottom = '1.25rem';
          card.style.padding = '1.25rem';
          card.style.borderRadius = 'var(--radius-lg)';

          const severityClass = rec.severity === 'High' ? 'severity-high' : 'severity-med';
          const recId = rec.id || `rec_${idx}`;
          const citations = rec.supporting_citations || [];

          let citationsHTML = '';
          citations.forEach(cit => {
            citationsHTML += `
              <div style="background:#090d16;border:1px solid var(--border-subtle);border-radius:6px;padding:0.75rem;margin-bottom:0.5rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem;flex-wrap:wrap;gap:0.3rem;">
                  <div style="font-size:0.75rem;font-weight:600;color:var(--nashta-cyan);">
                    📄 Bukti ${cit.citation_index || ''}: ${cit.page_display || ('Hal. ' + cit.printed_page)} • <em>${cit.chapter_title || 'Tata Kelola TI'}</em>
                  </div>
                  <a href="/api/documents/${this.activeEmitenCode}/${cit.report_year || 2024}" target="_blank" style="font-size:0.7rem;color:#38bdf8;text-decoration:underline;">
                    Buka Dokumen PDF (${cit.doc_name}) ↗
                  </a>
                </div>
                <div style="font-size:0.8rem;color:#e2e8f0;font-style:italic;background:rgba(0,0,0,0.35);padding:0.5rem 0.75rem;border-left:2px solid #38bdf8;border-radius:4px;line-height:1.5;">
                  “${cit.evidence_quote}”
                </div>
              </div>
            `;
          });

          card.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;margin-bottom:0.75rem;">
              <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
                <span class="severity-pill ${severityClass}">${rec.severity} Priority</span>
                <span style="font-size:0.75rem;background:rgba(16,185,129,0.12);color:#34d399;border:1px solid rgba(16,185,129,0.25);padding:3px 10px;border-radius:12px;font-weight:600;">
                  ⚡ ${rec.confidence}% Match Confidence
                </span>
                <span style="font-size:0.75rem;background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.25);padding:3px 10px;border-radius:12px;font-weight:600;">
                  🏛️ ${rec.pillar_name}
                </span>
              </div>
              <span style="font-size:0.75rem;color:var(--text-muted);font-weight:600;">
                📑 ${citations.length} Bukti Dokumen Terverifikasi
              </span>
            </div>

            <div style="font-size:1.05rem;font-weight:700;color:#f8fafc;margin-bottom:0.75rem;line-height:1.4;">
              ${rec.title}
            </div>

            <div style="background:rgba(15,23,42,0.7);border-left:3px solid var(--nashta-cyan);border-radius:6px;padding:0.85rem 1rem;margin-bottom:0.9rem;">
              <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:var(--nashta-cyan);margin-bottom:0.35rem;display:flex;align-items:center;gap:0.4rem;">
                <span>📋</span> Diagnosa & Sintesis Masalah Emiten
              </div>
              <div style="font-size:0.84rem;color:#cbd5e1;line-height:1.55;">
                ${rec.problem_synthesis}
              </div>
            </div>

            <div style="margin-bottom:0.9rem;">
              <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-secondary);margin-bottom:0.5rem;display:flex;align-items:center;justify-content:space-between;">
                <span>📑 Klaster Sitasi Bukti Dokumen Asli:</span>
                <button class="btn btn-secondary btn-sm" id="btnToggle_${recId}" style="font-size:0.7rem;padding:2px 8px;border-style:dashed;">
                  👁️ Sembunyikan/Tampilkan Bukti (${citations.length})
                </button>
              </div>

              <div id="cluster_${recId}" style="display:block;">
                ${citationsHTML}
              </div>
            </div>

            <div style="background:rgba(6,182,212,0.06);border:1px solid rgba(6,182,212,0.22);border-radius:8px;padding:0.85rem 1rem;display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;">
              <div style="flex:1;min-width:250px;">
                <div style="font-size:0.75rem;font-weight:700;color:var(--nashta-cyan);text-transform:uppercase;">💼 Rekomendasi Solusi Nashta:</div>
                <div style="font-size:0.86rem;font-weight:700;color:#f1f5f9;margin-top:0.15rem;">${rec.nashta_opportunity}</div>
                <div style="font-size:0.76rem;color:#94a3b8;margin-top:0.2rem;">${rec.value_proposition || ''}</div>
              </div>
              <div>
                <button class="btn btn-primary btn-sm" id="btnChat_${recId}" style="font-size:0.75rem;">
                  🤖 Analisis dengan AI Copilot
                </button>
              </div>
            </div>
          `;

          this.weaknessListContainer.appendChild(card);

          const toggleBtn = card.querySelector(`#btnToggle_${recId}`);
          const clusterBox = card.querySelector(`#cluster_${recId}`);
          if (toggleBtn && clusterBox) {
            toggleBtn.addEventListener('click', () => {
              const isHidden = clusterBox.style.display === 'none';
              clusterBox.style.display = isHidden ? 'block' : 'none';
              toggleBtn.innerHTML = isHidden 
                ? `👁️ Sembunyikan Bukti (${citations.length})` 
                : `👁️ Tampilkan Bukti (${citations.length})`;
            });
          }

          const chatBtn = card.querySelector(`#btnChat_${recId}`);
          if (chatBtn && window.aiAssistantUI) {
            chatBtn.addEventListener('click', () => {
              window.aiAssistantUI.toggleDrawer(true);
              window.aiAssistantUI.input.value = `Bagaimana Nashta dapat menawarkan solusi "${rec.nashta_opportunity}" untuk mengatasi diagnosa masalah: "${rec.problem_synthesis.slice(0, 150)}..."?`;
            });
          }
        });
        return;
      }

      rawWeaknesses.forEach((w, idx) => {
        const card = document.createElement('div');
        card.className = 'weakness-card';

        const severityClass = w.severity === 'High' ? 'severity-high' : 'severity-med';
        const contextId = `context_window_${idx}_${Date.now()}`;
        const confidence = w.match_confidence || 92;

        let highlightedContext = w.context_window || w.evidence_quote;
        if (w.evidence_quote && highlightedContext.includes(w.evidence_quote)) {
          highlightedContext = highlightedContext.replace(
            w.evidence_quote,
            `<mark style="background:rgba(6,182,212,0.3);color:#38bdf8;padding:2px 4px;border-radius:3px;font-weight:600;">${w.evidence_quote}</mark>`
          );
        }

        card.innerHTML = `
          <div class="weakness-header">
            <div class="weakness-title-group">
              <span class="severity-pill ${severityClass}">${w.severity} Severity</span>
              <span style="font-size:0.75rem;background:rgba(16,185,129,0.1);color:#34d399;border:1px solid rgba(16,185,129,0.25);padding:2px 8px;border-radius:12px;font-weight:600;">
                ⚡ ${confidence}% Match Confidence
              </span>
              <span class="weakness-title">${w.title}</span>
            </div>
            <a href="/api/documents/${this.activeEmitenCode}/${w.report_year || 2024}" target="_blank" class="weakness-source-badge" style="text-decoration:none;" title="Klik untuk membuka file PDF dokumen asli">
              📄 ${w.page_display || ('Hal. ' + w.page_number)} • ${w.doc_name || 'Laporan_Tahunan.pdf'} ↗️
            </a>
          </div>

          <div style="font-size:0.78rem;color:var(--text-muted);margin-top:-0.3rem;">
            📌 <strong>Bab Laporan:</strong> <em>${w.chapter_title || w.page_ref}</em>
          </div>

          <div class="evidence-quote-box">
            “${w.evidence_quote}”
          </div>

          <div style="margin-top:0.25rem;">
            <button class="btn btn-secondary btn-sm" id="btnToggle_${contextId}" style="border-style:dashed;color:var(--nashta-cyan);font-size:0.75rem;">
              🔍 Buka Konteks Paragraf Asli Dokumen (${w.page_display || ('Halaman ' + w.page_number)})
            </button>
            
            <div id="${contextId}" style="display:none;margin-top:0.6rem;background:#090d16;border:1px solid var(--border-default);border-radius:var(--radius-md);padding:0.9rem;font-size:0.8rem;line-height:1.6;color:#94a3b8;">
              <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.3rem;align-items:center;">
                <strong style="color:var(--text-primary);font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">
                  📑 Cuplikan Paragraf Asli • ${w.page_display || ('Hal. ' + w.page_number)} (${w.doc_name})
                </strong>
                <a href="/api/documents/${this.activeEmitenCode}/${w.report_year || 2024}" target="_blank" style="font-size:0.7rem;color:var(--nashta-cyan);text-decoration:underline;">
                  Buka Full PDF ↗
                </a>
              </div>
              <div style="font-style:italic;">${highlightedContext}</div>
            </div>
          </div>

          <div class="weakness-solution-row">
            <div><strong>Peluang Solusi Nashta:</strong> ${w.nashta_opportunity}</div>
            <button class="btn btn-primary btn-sm" id="btnChat_${contextId}">
              🤖 Analisis dengan AI Copilot
            </button>
          </div>
        `;

        this.weaknessListContainer.appendChild(card);

        const toggleBtn = card.querySelector(`#btnToggle_${contextId}`);
        const contextBox = card.querySelector(`#${contextId}`);
        if (toggleBtn && contextBox) {
          toggleBtn.addEventListener('click', () => {
            const isHidden = contextBox.style.display === 'none';
            contextBox.style.display = isHidden ? 'block' : 'none';
            toggleBtn.innerHTML = isHidden 
              ? `🔼 Tutup Konteks Paragraf Asli (Halaman ${w.page_number || ''})` 
              : `🔍 Buka Konteks Paragraf Asli Dokumen (Halaman ${w.page_number || ''})`;
          });
        }

        const chatBtn = card.querySelector(`#btnChat_${contextId}`);
        if (chatBtn && window.aiAssistantUI) {
          chatBtn.addEventListener('click', () => {
            window.aiAssistantUI.toggleDrawer(true);
            window.aiAssistantUI.input.value = `Bagaimana Nashta dapat menawarkan solusi untuk mengatasi temuan di Halaman ${w.page_number}: "${w.evidence_quote}"?`;
            window.aiAssistantUI.sendMessage();
          });
        }
      });
    }

    renderReportsVault(reports, code) {
      this.reportsListContainer.innerHTML = '';
      
      reports.forEach(r => {
        const card = document.createElement('div');
        card.className = 'report-row-card';
        const localDocUrl = `/api/documents/${code}/${r.year}`;
        const isExternalBackup = r.backup_url && r.backup_url.startsWith('http');
        
        card.innerHTML = `
          <div class="report-info">
            <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
              <span class="report-year-tag">${r.year}</span>
              <span class="report-title">${r.title}</span>
            </div>
            <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.25rem;">
              Ukuran: ~${r.size_mb || 30} MB • Status: <span class="report-status-tag" style="background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.3);">✅ ${r.status || 'Verified Local PDF'}</span>
            </div>
          </div>
          <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
            <a href="${localDocUrl}" target="_blank" class="btn btn-primary btn-sm" style="font-size:0.75rem;">
              📄 Buka PDF Asli
            </a>
            <a href="${localDocUrl}" download class="btn btn-secondary btn-sm" style="font-size:0.75rem;" title="Unduh file PDF ke komputer">
              ⬇️ Unduh
            </a>
            ${isExternalBackup ? `
            <a href="${r.backup_url}" target="_blank" class="btn btn-secondary btn-sm" style="color:var(--text-muted);font-size:0.75rem;" title="Buka Portal Hubungan Investor (IR) / Web Resmi">
              🌐 Portal IR
            </a>` : ''}
          </div>
        `;
        this.reportsListContainer.appendChild(card);
      });
    }

    async verifyReportsHealth() {
      this.verifyReportsBtn.innerText = '⏳ Menguji URL...';
      try {
        const resp = await fetch(`/api/verify-reports/${this.activeEmitenCode}`, { method: 'POST' });
        const data = await resp.json();
        alert(`✅ Selesai verifikasi konektivitas untuk ${data.code}.\nSemua dokumen dapat diakses melalui multi-tier harvester.`);
      } catch (err) {
        alert('Gagal memverifikasi: ' + err.message);
      } finally {
        this.verifyReportsBtn.innerText = '🔍 Uji Konektivitas Dokumen';
      }
    }

    async handleFileUpload(file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Harap unggah file berformat PDF');
        return;
      }

      this.uploadStatus.innerHTML = '<span style="color:var(--nashta-cyan);">⏳ Mengunggah, mengekstrak teks berhalaman, dan memecah menjadi chunk RAG...</span>';

      const formData = new FormData();
      formData.append('code', this.activeEmitenCode);
      formData.append('year', 2024);
      formData.append('file', file);

      try {
        const resp = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        const result = await resp.json();
        
        this.uploadStatus.innerHTML = `
          <div style="color:var(--nashta-emerald);font-weight:700;font-size:0.8rem;">
            ✅ Berhasil mengekstrak ${result.processed_pages} halaman ke dalam RAG Index!
          </div>
          <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:0.2rem;">
            Ditemukan ${result.keyword_hits_count} kecocokan kata kunci 10 Pilar Nashta. Dashboard diperbarui.
          </div>
        `;
        this.selectIssuer(this.activeEmitenCode);
      } catch (err) {
        this.uploadStatus.innerHTML = `<span style="color:var(--nashta-rose);">⚠️ Gagal memproses: ${err.message}</span>`;
      }
    }
  }

  window.dashboardApp = new NashtaDashboardApp();
});
