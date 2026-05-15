/* ============================================================
   ExamProctor — UI Enhancement Script
   Handles: sidebar toggle, tooltips, animations, mobile nav
   ============================================================ */

   document.addEventListener('DOMContentLoaded', function () {

    // ── Mobile Sidebar Toggle ──────────────────────────────────
    const sidebar  = document.querySelector('.sidebar');
    const overlay  = document.querySelector('.sidebar-overlay');
    const menuBtn  = document.getElementById('sidebar-toggle');
  
    if (menuBtn && sidebar && overlay) {
      menuBtn.addEventListener('click', function () {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
      });
      overlay.addEventListener('click', function () {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
      });
    }
  
    // ── Auto-dismiss Flash Alerts ──────────────────────────────
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
      setTimeout(function () {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }, 4500);
    });
  
    // ── Animate Stat Cards on Scroll ──────────────────────────
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-up');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
  
    document.querySelectorAll('.stat-card').forEach(function (card) {
      observer.observe(card);
    });
  
    // ── Animate Number Counters ────────────────────────────────
    document.querySelectorAll('.stat-value[data-count]').forEach(function (el) {
      const target   = parseInt(el.dataset.count, 10);
      const duration = 800;
      const step     = target / (duration / 16);
      let current    = 0;
  
      const timer = setInterval(function () {
        current += step;
        if (current >= target) {
          el.textContent = target;
          clearInterval(timer);
        } else {
          el.textContent = Math.floor(current);
        }
      }, 16);
    });
  
    // ── Confirm Delete Buttons ─────────────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        if (!confirm(el.dataset.confirm)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
    });
  
    // ── Tooltip Initialisation (Bootstrap) ────────────────────
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(function (el) {
      new bootstrap.Tooltip(el, { placement: 'top' });
    });
  
    // ── Password Visibility Toggle ─────────────────────────────
    document.querySelectorAll('.toggle-password').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const target = document.getElementById(btn.dataset.target);
        if (!target) return;
        const isText  = target.type === 'text';
        target.type   = isText ? 'password' : 'text';
        btn.innerHTML = isText
          ? '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/><path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/></svg>'
          : '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7 7 0 0 0-2.79.588l.77.771A6 6 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755q-.247.248-.517.486z"/><path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829zm-2.943 1.299.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829"/><path d="M3.35 5.47q-.27.24-.518.487A13 13 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7 7 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709zm10.296 8.884-12-12 .708-.708 12 12z"/></svg>';
      });
    });
  
    // ── Exam option highlight (replaces inline JS) ─────────────
    document.querySelectorAll('input[type="radio"].option-radio').forEach(function (radio) {
      radio.addEventListener('change', function () {
        const name = this.name;
        // Reset all labels in this group
        document.querySelectorAll(`input[name="${name}"].option-radio`).forEach(function (r) {
          const lbl = r.closest('.option-label');
          if (lbl) lbl.classList.remove('selected');
        });
        // Activate chosen label
        const chosenLbl = this.closest('.option-label');
        if (chosenLbl) chosenLbl.classList.add('selected');
      });
    });
  
  });