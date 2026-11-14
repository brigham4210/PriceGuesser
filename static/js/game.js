(function () {
    'use strict';

    // Format the guess with commas while typing. The server also accepts "450k".
    var guessInput = document.getElementById('guessInput');
    if (guessInput) {
        guessInput.addEventListener('input', function (e) {
            var raw = e.target.value;
            if (/[km]\s*$/i.test(raw)) return;
            var digits = raw.replace(/\D/g, '');
            e.target.value = digits ? '$' + parseInt(digits, 10).toLocaleString('en-US') : '';
        });
    }

    // Photo carousel: one photo at a time, buttons plus left/right arrow keys.
    var carousel = document.querySelector('[data-carousel]');
    if (carousel) {
        var slides = carousel.querySelectorAll('.slide');
        var controls = carousel.querySelector('.carousel-controls');
        var count = carousel.querySelector('[data-count]');
        var index = 0;
        if (slides.length > 1) {
            carousel.classList.add('is-enhanced');
            controls.hidden = false;
            carousel.tabIndex = 0;
            var show = function (i) {
                index = (i + slides.length) % slides.length;
                slides.forEach(function (s, n) { s.classList.toggle('is-active', n === index); });
                count.textContent = (index + 1) + ' / ' + slides.length;
            };
            carousel.querySelector('[data-prev]').addEventListener('click', function () { show(index - 1); });
            carousel.querySelector('[data-next]').addEventListener('click', function () { show(index + 1); });
            carousel.addEventListener('keydown', function (e) {
                if (e.target.tagName === 'INPUT') return;
                if (e.key === 'ArrowLeft') { e.preventDefault(); show(index - 1); }
                if (e.key === 'ArrowRight') { e.preventDefault(); show(index + 1); }
            });
            show(0);
        }
    }

    // Best score, kept in this browser only.
    var final = document.querySelector('[data-final-score]');
    var bestEl = document.querySelector('[data-best-score]');
    if (final && bestEl) {
        var score = parseInt(final.getAttribute('data-final-score'), 10) || 0;
        var best = 0;
        try { best = parseInt(localStorage.getItem('priceguesser.bestScore'), 10) || 0; } catch (e) { /* storage blocked */ }
        if (score > best) {
            try { localStorage.setItem('priceguesser.bestScore', String(score)); } catch (e) { /* storage blocked */ }
            bestEl.textContent = best ? 'New best score! Your previous best was ' + best.toLocaleString('en-US') + '.' : 'This is your first recorded score.';
        } else {
            bestEl.textContent = 'Your best score in this browser: ' + best.toLocaleString('en-US') + '.';
        }
    }
})();
