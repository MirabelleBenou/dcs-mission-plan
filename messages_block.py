#!/usr/bin/env python3
"""Bloc « MESSAGES COMMUNS » : le toast de la suite, écrit une fois, injecté tel quel dans les six modules qui parlent par toast
(HQ, Route Planner, Briefing Generator, Datacard Generator, Flight Configurator, Recon Station).

Deux textes, identiques à l'octet dans les six dist/ :
  build_css()   — la feuille du toast (bas centré à --mp-toast-bottom, 20 px par défaut ; fond --olive-dark ; liseré 1 px, 4 px à gauche ;
                  Oswald 500 ; la couleur du liseré porte le type : ambre (info), vert --green-radar (ok), --mp-warn (err : la couleur d'avertissement de ui_block.py))
  build_block() — le script : showToast(msg, opts), showToastAction(msg, label, fn, ms) (raccourci de showToast)

L'appel : showToast(msg, opts).
  opts absent ou nombre → info, durée = ce nombre ou 2 200 ms (les appels d'avant le bloc restent valides)
  opts objet            → { type: 'ok' | 'err', ms, action: { label, fn } }
Durées : info et ok 2 200 ms par défaut ; err 5 000 ms au moins (une valeur plus courte est portée à 5 000) ; avec action 12 000 ms par défaut.
Un clic sur l'action appelle fn puis ferme le toast (sauf si fn a montré un autre toast). Un seul toast à la fois : un nouvel appel remplace le précédent.
Un seul élément #toast (role="status", aria-live="polite" ; "assertive" pendant un toast err), créé par le bloc.
Le texte d'un toast err commence par « ⚠ » dans le dictionnaire du module : le bloc n'ajoute rien au texte.
Le module qui a une commande en bas de l'écran pose --mp-toast-bottom (Recon Station : 12 px au-dessus de l'aide de dessin ou de la barre de dessin).

Usage (par les builds) : from messages_block import build_block, build_css
"""

BLOCK_BEGIN = '/* ===== MESSAGES COMMUNS (toast) ===== */'
BLOCK_END = '/* ===== FIN DES MESSAGES COMMUNS ===== */'
CSS_BEGIN = '/* ===== MESSAGES COMMUNS : feuille du toast ===== */'
CSS_END = '/* ===== FIN DE LA FEUILLE DU TOAST ===== */'

_CSS = r"""
.toast {
  position: fixed; bottom: var(--mp-toast-bottom, 20px); left: 50%;
  transform: translateX(-50%) translateY(100px);
  background: var(--olive-dark); border: 1px solid var(--amber); border-left-width: 4px;
  color: var(--paper); font-family: var(--f-ui); font-weight: 500; letter-spacing: 2px; text-transform: uppercase; font-size: 12px;
  padding: 10px 20px; z-index: 20000; opacity: 0; visibility: hidden; pointer-events: none;
  transition: opacity .3s ease, transform .3s ease, visibility 0s linear .3s;
  box-shadow: 0 4px 16px rgba(0,0,0,.6); width: max-content; max-width: calc(100vw - 24px); text-align: center;
}
.toast.show { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); transition-delay: 0s; }
.toast.show.act { pointer-events: auto; }
.toast.ok { border-color: var(--green-radar); }
.toast.err { border-color: var(--mp-warn, #e8806a); }
.toast-action {
  background: none; border: 0; padding: 6px 4px; margin: -6px 0; cursor: pointer;
  font: inherit; letter-spacing: inherit; text-transform: inherit; color: var(--amber);
  text-decoration: underline; text-underline-offset: 3px;
}
.toast-action:hover, .toast-action:focus-visible { color: var(--paper-light, var(--paper)); }
@media print { .toast { display: none !important; } }
"""

_JS = r"""
function mpToastEl() {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast'; el.className = 'toast';
    el.setAttribute('role', 'status'); el.setAttribute('aria-live', 'polite');
    (document.body || document.documentElement).appendChild(el);
  }
  return el;
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mpToastEl); else mpToastEl();
function mpToastHide(el) {
  el.classList.remove('show', 'act');
  setTimeout(() => { if (!el.classList.contains('show')) el.textContent = ''; }, 400);
}
function showToast(msg, opts) {
  const el = mpToastEl();
  const o = (opts && typeof opts === 'object') ? opts : { ms: (typeof opts === 'number') ? opts : 0 };
  const type = (o.type === 'ok' || o.type === 'err') ? o.type : '';
  const act = (o.action && typeof o.action.fn === 'function') ? o.action : null;
  let ms = (o.ms > 0) ? o.ms : (act ? 12000 : 2200);
  if (type === 'err' && ms < 5000) ms = 5000;
  const n = (showToast._n || 0) + 1;
  showToast._n = n;
  clearTimeout(showToast._h);
  el.textContent = '';
  const m = document.createElement('span');
  m.textContent = (act ? msg + ' ' : String(msg));
  el.appendChild(m);
  if (act) {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'toast-action'; b.textContent = act.label;
    b.addEventListener('click', () => {
      try { act.fn(); } finally { if (showToast._n === n) { clearTimeout(showToast._h); mpToastHide(el); } }
    });
    el.appendChild(b);
  }
  el.setAttribute('aria-live', type === 'err' ? 'assertive' : 'polite');
  el.className = 'toast show' + (type ? ' ' + type : '') + (act ? ' act' : '');
  showToast._h = setTimeout(() => { if (showToast._n === n) mpToastHide(el); }, ms);
}
function showToastAction(msg, label, fn, ms) { showToast(msg, { action: { label: label, fn: fn }, ms: ms }); }
"""


def build_block():
    """Le script du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


def build_css():
    """La feuille du bloc, délimitée par ses deux commentaires, terminée par un saut de ligne."""
    return CSS_BEGIN + _CSS + CSS_END + '\n'


if __name__ == '__main__':
    print(f"[OK] bloc de messages : script {len(build_block())} caractères, feuille {len(build_css())}")
