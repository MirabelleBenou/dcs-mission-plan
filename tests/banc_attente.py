"""Aide commune d'attente du banc : attendre un état, jamais une durée.
Chaque attente a un délai maximal (DELAI, 15 s par défaut ; un appel peut en demander plus pour un calcul long) et, à l'échec, lève une AssertionError qui dit l'état attendu et l'état lu.
Les états sont ceux que l'application pose déjà (`S.theatre`, `__RP.thr`, `__RP.prof`, `SP`, le cadre chargé et sa barre) ; aucun drapeau n'est ajouté à l'application.
`cible` est une page (le shell) ou un cadre (un outil)."""
from playwright.sync_api import TimeoutError as PWTimeout

DELAI = 15000

# --- les expressions d'état (des fonctions : elles reçoivent un argument au besoin) ---
OUTIL = """(tid) => { const f = document.getElementById('iframe-' + tid), ld = document.getElementById('module-loading');
  if (!f || f.style.display === 'none' || activeModule !== tid || !ld || !ld.classList.contains('hidden')) return false;
  const d = f.contentDocument;
  return !!d && d.readyState === 'complete' && (!d.querySelector('.toolbar') || !!d.querySelector('.toolbar .mp-back-injected')); }"""
OUTIL_LU = """(tid) => { const f = document.getElementById('iframe-' + tid), ld = document.getElementById('module-loading'), d = f && f.contentDocument;
  return { iframe: !!f, display: f ? f.style.display : null, actif: activeModule, charge: ld ? ld.className : null, ready: d ? d.readyState : null,
    toolbar: d ? !!d.querySelector('.toolbar') : null, retour: d ? !!d.querySelector('.toolbar .mp-back-injected') : null }; }"""
RP_PRET = """() => typeof window.__RP !== 'undefined' && typeof mapCreated !== 'undefined' && mapCreated === true && __RP.map.getSize().x > 0 && __RP.map.getSize().y > 0"""
RP_PRET_LU = """() => ({ rp: typeof window.__RP !== 'undefined', creee: typeof mapCreated !== 'undefined' ? mapCreated : null, taille: typeof window.__RP !== 'undefined' ? __RP.map.getSize() : null })"""
THEATRE = "(n) => typeof S !== 'undefined' && !!S && S.theatre === n"
THEATRE_LU = "() => typeof S !== 'undefined' && S ? S.theatre : '(S absent)'"
VUE = """() => { const m = __RP.map, s = m.getSize(); if (!(s.x > 0 && s.y > 0)) return false; const c = m.getCenter(), k = c.lat + '|' + c.lng + '|' + m.getZoom() + '|' + s.x + 'x' + s.y;
  const avant = window.__banc_vue; window.__banc_vue = k; return avant === k; }"""
VUE_LU = "() => { const m = __RP.map, c = m.getCenter(), s = m.getSize(); return { centre: [c.lat, c.lng], zoom: m.getZoom(), taille: [s.x, s.y], derniere_lecture: window.__banc_vue }; }"
MENACES = "() => { const T = __RP.thr; return T.state === 'ok' && T.jobs.size === 0 && T.act.length > 0 && T.grids.size === T.act.length; }"
MENACES_LU = "() => { const T = __RP.thr; return { state: T.state, jobs: T.jobs.size, actives: T.act.length, grilles: T.grids.size }; }"
PROFIL = "() => { const P = __RP.prof; return !!P.data && !P.data.fail && P.data.key === profKey() && !!P.view; }"
PROFIL_LU = "() => { const P = __RP.prof; return { data: !!P.data, fail: P.data ? !!P.data.fail : null, cle_lue: P.data ? P.data.key : null, cle_attendue: profKey(), vue: !!P.view }; }"
IMAGES = "(n) => { window.__banc_img = (window.__banc_img || 0) + 1; return window.__banc_img > n; }"


def _lire(cible, lecture, arg=None):
    try:
        return cible.evaluate(lecture, arg)
    except Exception as e:                       # la page est partie, ou plantée : on le dit au lieu de masquer l'échec
        return '(illisible : %s)' % str(e).split('\n')[0][:120]


def attendre_etat(cible, expr, etat, lecture=None, arg=None, delai=DELAI, polling='raf'):
    """Attend que `expr` (une fonction JavaScript qui rend vrai) le soit dans `cible`. À l'échec : l'état attendu (`etat`) et l'état lu (`lecture`, une fonction JavaScript ; à défaut, la valeur de `expr`)."""
    try:
        cible.wait_for_function(expr, arg=arg, timeout=delai, polling=polling)
    except PWTimeout:
        raise AssertionError('état attendu : %s ; état lu : %s (délai %d ms)' % (etat, _lire(cible, lecture or expr, arg), delai)) from None


def attendre_images(cible, n=2, delai=DELAI):
    """Attend n images de rendu de la page ou du cadre (les ResizeObserver et la mise en page ont passé) ; un cadre caché n'en reçoit pas : l'échec le dit."""
    cible.evaluate('() => { window.__banc_img = 0; }')
    attendre_etat(cible, IMAGES, '%d images de rendu écoulées' % n, lecture='() => window.__banc_img', arg=n, delai=delai)


SHELL_PRET = """() => document.readyState === 'complete' && typeof NAV !== 'undefined' && typeof openModule === 'function' && typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-hq')"""
SHELL_PRET_LU = """() => ({ ready: document.readyState, nav: typeof NAV, openModule: typeof openModule, exemple: typeof window.MP_WORK_EXAMPLE, carte_hq: !!document.getElementById('card-hq') })"""


def attendre_shell(pg, delai=30000):
    """Le shell est chargé (page complète, navigation, exemples de travail, cartes de l'accueil) ; le premier chargement d'un fichier de 17 Mo peut passer 15 s sur une machine chargée."""
    attendre_etat(pg, SHELL_PRET, "le shell chargé (page complète, NAV, openModule, MP_WORK_EXAMPLE, cartes de l'accueil)", lecture=SHELL_PRET_LU, delai=delai)


def exemple(pg, groupe):
    """Pose l'exemple d'un groupe (MP_WORK_EXAMPLE rend vrai quand les clés du groupe sont écrites)."""
    ok = pg.evaluate('(g) => window.MP_WORK_EXAMPLE(g)', groupe)
    assert ok is True, "l'exemple du groupe %s n'a pas été posé (MP_WORK_EXAMPLE a rendu %r)" % (groupe, ok)


def attendre_outil(pg, tid, delai=DELAI):
    """L'outil `tid` est ouvert dans le shell : son cadre est chargé et affiché, sa barre posée (bouton retour injecté). Rend le cadre."""
    attendre_etat(pg, OUTIL, "l'outil %s ouvert (cadre chargé et affiché, barre posée)" % tid, lecture=OUTIL_LU, arg=tid, delai=delai)
    return pg.query_selector('#iframe-' + tid).content_frame()


def attendre_rp(pg, delai=DELAI):
    """Le Route Planner est ouvert et sa carte créée, à une taille non nulle. Rend le cadre."""
    fr = attendre_outil(pg, 'rp', delai)
    attendre_etat(fr, RP_PRET, 'le Route Planner prêt (window.__RP posé, carte créée à une taille non nulle)', lecture=RP_PRET_LU, delai=delai)
    attendre_images(fr, 2, delai)
    return fr


def attendre_theatre(fr, nom, delai=DELAI, polling='raf'):
    """S.theatre vaut `nom` ; polling=100 pour un outil caché par le shell (un cadre caché ne reçoit pas d'images de rendu)."""
    attendre_etat(fr, THEATRE, "S.theatre === '%s'" % nom, lecture=THEATRE_LU, arg=nom, delai=delai, polling=polling)


def attendre_vue_stable(fr, delai=DELAI):
    """La vue de la carte du RP est stable : deux lectures égales (centre, zoom, taille) à 100 ms d'écart."""
    fr.evaluate('() => { window.__banc_vue = null; }')
    attendre_etat(fr, VUE, 'la vue de la carte stable (deux lectures égales du centre et du zoom à 100 ms)', lecture=VUE_LU, delai=delai, polling=100)


def attendre_menaces(fr, delai=30000):
    attendre_etat(fr, MENACES, 'les menaces prêtes (état ok, aucun calcul en cours, une grille par menace active)', lecture=MENACES_LU, delai=delai)


def attendre_profil(fr, delai=60000):
    attendre_etat(fr, PROFIL, 'le profil prêt (données de la clé courante, vue posée)', lecture=PROFIL_LU, delai=delai)


# --- attentes courtes : une expression JavaScript (pas une fonction), `arg` y est lu comme `arg` ---
def attendre(cible, expr, etat=None, lu=None, arg=None, delai=DELAI, polling='raf'):
    """Attend que l'expression JavaScript `expr` soit vraie dans `cible` ; `etat` la dit en clair (par défaut `expr`), `lu` est une expression JavaScript qui décrit ce que l'application montre à l'échec (par défaut la valeur de `expr`)."""
    attendre_etat(cible, '(arg) => (%s)' % expr, etat or expr, lecture='(arg) => (%s)' % (lu or expr), arg=arg, delai=delai, polling=polling)


# --- l'état de mise en page du Route Planner : ce que l'application pose elle-même (SP) ---
# la carte en grand (cadre d'export, dessin) : jusqu'à 1 100 px, la classe rp-mapfull suit SP.full ; la dernière vue vue (SP.view) est rafraîchie à chaque moveend tant que la carte a une taille
MISE_EN_PAGE = """!SP.mq.matches || (document.body.classList.contains('rp-mapfull') === !!(SP.full.exp || SP.full.dr) && !SP.away && SP.hold === null
  && (!SP.view || (SP.view.z === __RP.map.getZoom() && SP.view.c.lat === __RP.map.getCenter().lat && SP.view.c.lng === __RP.map.getCenter().lng)))"""
MISE_EN_PAGE_LU = """({ mq: SP.mq.matches, mapfull: document.body.classList.contains('rp-mapfull'), full: SP.full, away: SP.away, hold: SP.hold && { z: SP.hold.z }, view: SP.view && { z: SP.view.z, lat: SP.view.c.lat },
  carte: { z: __RP.map.getZoom(), lat: __RP.map.getCenter().lat } })"""


def attendre_mise_en_page(fr, delai=DELAI):
    """Le Route Planner a fini de se mettre en page après un geste : des images de rendu sont passées, SP est au repos (pas d'absence en cours, la classe de la carte en grand suit SP.full, la dernière vue vue est celle de la carte) et la vue est stable."""
    attendre_images(fr, 3, delai)
    attendre(fr, MISE_EN_PAGE, "la mise en page du Route Planner au repos (SP : carte en grand, absence, dernière vue vue)", lu=MISE_EN_PAGE_LU, delai=delai)
    attendre_vue_stable(fr, delai)


def viser(fr, lat, lon, zoom, delai=DELAI):
    """Pose la vue sans animation et attend qu'elle soit celle de la carte, retenue et stable."""
    fr.evaluate('([la, lo, z]) => __RP.map.setView([la, lo], z, { animate: false })', [lat, lon, zoom])
    attendre(fr, '__RP.map.getZoom() === arg[2] && Math.abs(__RP.map.getCenter().lat - arg[0]) < 1e-6 && Math.abs(__RP.map.getCenter().lng - arg[1]) < 1e-6', 'la vue posée : centre et zoom',
             lu='({ z: __RP.map.getZoom(), lat: __RP.map.getCenter().lat, lng: __RP.map.getCenter().lng })', arg=[lat, lon, zoom], delai=delai)
    attendre_mise_en_page(fr, delai)


def poser_mode(fr, mode, delai=DELAI):
    """Change le mode de toucher du Route Planner (lire, dessin, règle...) et attend l'état : le mode posé, la carte remise en page."""
    fr.evaluate('(m) => setTapMode(m)', mode)
    attendre(fr, 'tapMode === arg', "le mode de toucher '%s'" % mode, lu='tapMode', arg=mode, delai=delai)
    attendre_mise_en_page(fr, delai)


def cadre_export(fr, ouvert, delai=DELAI):
    """Ouvre ou ferme le cadre d'export et attend l'état : EXP.on posé, la carte remise en page."""
    fr.evaluate('expOpen()' if ouvert else 'expClose()')
    attendre(fr, 'EXP.on === arg', "le cadre d'export %s (EXP.on === %s)" % ('ouvert' if ouvert else 'fermé', 'true' if ouvert else 'false'), lu='EXP.on', arg=ouvert, delai=delai)
    attendre_mise_en_page(fr, delai)


def quitter_rp(pg, autre, delai=DELAI):
    """Le shell montre un autre outil : celui-ci est ouvert (chargé, affiché, barre posée) et le Route Planner est caché. Rend le cadre de l'autre outil."""
    pg.evaluate('(o) => openModule(o)', autre)
    fr2 = attendre_outil(pg, autre, delai)
    attendre(pg, "document.getElementById('iframe-rp').style.display === 'none'", "le cadre du Route Planner caché", delai=delai)
    return fr2


def revenir_rp(pg, fr, delai=DELAI):
    """Le shell réaffiche le Route Planner : son cadre est affiché, ses ResizeObserver ont passé, SP est au repos, la vue est stable."""
    pg.evaluate("openModule('rp')")
    attendre_outil(pg, 'rp', delai)
    attendre_mise_en_page(fr, delai)


def attendre_fenetre(cible, w, h, delai=DELAI):
    """La page (ou le cadre) a la taille de fenêtre demandée et des images de rendu sont passées (après set_viewport_size)."""
    attendre(cible, 'innerWidth === arg[0] && innerHeight === arg[1]', 'la fenêtre à %d × %d' % (w, h), lu='[innerWidth, innerHeight]', arg=[w, h], delai=delai)
    attendre_images(cible, 3, delai)


# --- le Route Planner au repos : le profil et les menaces ont fini de se dessiner ---
# lecture comparée à la précédente (polling 100 ms) : la signature du dernier dessin du profil (PROF.rsig), la hauteur du bandeau, la longueur de son SVG, sa boîte et celle de la carte, la version et l'état des menaces
REPOS = """() => { const P = __RP.prof, T = __RP.thr, s = document.querySelector('#rp-prof .prof-svg'), p = document.getElementById('rp-prof'), r = p ? p.getBoundingClientRect() : null, m = __RP.map.getSize();
  if (DISP.threats && T.state === 'ok' && T.jobs.size > 0) return false;
  const k = JSON.stringify([P.rsig, P.shown, P.h, s ? s.innerHTML.length : -1, r && [r.x, r.y, r.width, r.height], m.x, m.y, T.ver, T.state, T.jobs.size, S.points.length, S.theatre]);
  const avant = window.__banc_repos; window.__banc_repos = k; return avant === k; }"""
REPOS_LU = """() => { const P = __RP.prof, T = __RP.thr; return { rsig_court: String(P.rsig).slice(0, 60), shown: P.shown, h: P.h, menaces: [T.state, T.jobs.size, T.ver], derniere_lecture: String(window.__banc_repos).slice(0, 120) }; }"""


def attendre_repos(fr, delai=DELAI):
    """Le Route Planner est au repos après un geste : des images de rendu sont passées, aucun calcul de menaces n'est en cours, et deux lectures du dernier dessin du profil, des boîtes de la carte et du bandeau, à 100 ms d'écart, sont égales."""
    attendre_images(fr, 2, delai)
    fr.evaluate('() => { window.__banc_repos = null; }')
    attendre_etat(fr, REPOS, 'le Route Planner au repos (dessin du profil, boîtes, menaces : deux lectures égales à 100 ms)', lecture=REPOS_LU, delai=delai, polling=100)


def attendre_profil_repos(fr, zones=False, delai=60000):
    """Le profil est prêt (clé courante, vue posée) et dessiné : le Route Planner est au repos ; zones=True attend en plus qu'au moins une zone de menace soit dessinée."""
    attendre_profil(fr, delai)
    if zones:
        attendre(fr, '__RP.prof.zones.length > 0 && document.querySelectorAll("path.prof-zone").length > 0', 'au moins une zone de menace dessinée dans le profil', lu='[__RP.prof.zones.length, document.querySelectorAll("path.prof-zone").length]', delai=delai)
    attendre_repos(fr, delai)


# --- la barre d'outils « ⋯ » (UIMORE) dans un DOM fabriqué (test_barre_plus) ---
BARRE_PRETE = "() => typeof UIMORE !== 'undefined' && UIMORE.sig !== '' && !!document.querySelector('.tb-more-btn') && document.querySelector('.tb-more-btn').getBoundingClientRect().width > 0"
BARRE_PRETE_LU = "() => ({ uimore: typeof UIMORE, sig: typeof UIMORE !== 'undefined' ? UIMORE.sig : null, bouton: !!document.querySelector('.tb-more-btn') })"
BARRE = """() => { const tb = document.querySelector('.toolbar'); if (!tb) return false; const m = tb.querySelector('.tb-more-btn'), r = m ? m.getBoundingClientRect() : null, p = document.querySelector('.tb-more-panel');
  const k = JSON.stringify([UIMORE.sig, tb.className, tb.scrollWidth, tb.clientWidth, r && [r.x, r.right], !!p, p ? p.getAttribute('data-key') : null, tb.querySelectorAll('[data-mp-off]').length]);
  const avant = window.__banc_barre; window.__banc_barre = k; return avant === k; }"""


def attendre_barre_prete(pg, delai=DELAI):
    """La barre fabriquée a pris sa décision (UIMORE.sig posé, « ⋯ » affiché) et ne bouge plus."""
    attendre_etat(pg, BARRE_PRETE, 'la barre prête (UIMORE.sig posé, « ⋯ » affiché)', lecture=BARRE_PRETE_LU, delai=delai)
    attendre_barre_stable(pg, delai)


def attendre_barre_stable(pg, delai=DELAI):
    """La barre au repos après un geste ou une mutation : des images de rendu sont passées et deux lectures (décision, classes, largeurs, « ⋯ », menu ouvert) à 100 ms d'écart sont égales."""
    attendre_images(pg, 2, delai)
    pg.evaluate('() => { window.__banc_barre = null; }')
    attendre_etat(pg, BARRE, 'la barre au repos (décision, classes, largeurs, « ⋯ », menu : deux lectures égales à 100 ms)',
                  lecture='() => ({ sig: UIMORE.sig, classes: document.querySelector(".toolbar").className, derniere_lecture: String(window.__banc_barre).slice(0, 160) })', delai=delai, polling=100)


# --- le relief du Route Planner (case Relief, altitude du sol au pointeur) ---
# la couche suit la case et le théâtre : le théâtre voulu est posé (RE.key) et sa description est arrivée (couche posée) ou a échoué (toast une fois annoncé)
RELIEF_POSE = "RE.key === (DISP.relief && reliefTheatre(S.theatre) ? S.theatre : '') && (RE.key === '' || !!RE.layer || RE.toasted.has(RE.key))"
RELIEF_POSE_LU = "[RE.key, DISP.relief, S.theatre, !!RE.layer, [...RE.toasted]]"
RELIEF_REPOS = """() => { if (RE.raf !== 0 || RE.dwell !== 0 || RE.pend !== '') return false; const b = document.getElementById('rp-alt'), x = document.getElementById('rp-alt-x');
  const k = JSON.stringify([!!b && !b.hidden, b ? b.textContent : '', !!x && !x.hidden, RE.tiles.size, RE.shown && RE.shown.kind]); const avant = window.__banc_relief; window.__banc_relief = k; return avant === k; }"""


def attendre_relief_pose(fr, delai=DELAI):
    """La couche de relief suit l'état voulu (case, théâtre) : posée, absente, ou en échec annoncé ; puis des images de rendu."""
    attendre(fr, RELIEF_POSE, 'la couche de relief posée comme la case et le théâtre le veulent (RE)', lu=RELIEF_POSE_LU, delai=delai)
    attendre_images(fr, 2, delai)


def attendre_relief_repos(fr, delai=DELAI):
    """Le relief au repos après un mouvement du pointeur ou un toucher : l'image de lecture est passée, aucune attente de tuile (RE.dwell), aucune lecture en cours (RE.pend), le cartouche ne change plus."""
    attendre_images(fr, 2, delai)
    fr.evaluate('() => { window.__banc_relief = null; }')
    attendre_etat(fr, RELIEF_REPOS, 'le relief au repos (RE.raf, RE.dwell, RE.pend nuls, cartouche stable sur deux lectures à 100 ms)',
                  lecture="() => ({ raf: RE.raf, dwell: RE.dwell, pend: RE.pend, derniere_lecture: window.__banc_relief })", delai=delai, polling=100)
