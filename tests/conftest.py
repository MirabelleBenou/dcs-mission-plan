"""Commun à tous les tests du dossier : chaque test ferme les contextes de navigateur qu'il a ouverts.
Un shell construit pèse plusieurs dizaines de Mo de tas JavaScript et un processus de rendu par page : des contextes jamais fermés s'empilent dans le navigateur du fichier
(module, un Chromium par fichier) et, vers le quarantième, le rendu d'une page meurt (« Target crashed »)."""
import pytest


@pytest.fixture(autouse=True)
def _ferme_les_contextes(request):
    yield
    br = request.node.funcargs.get('browser') if hasattr(request.node, 'funcargs') else None
    if br is None:        # pas de navigateur dans ce test, ou il ne s'est pas lancé : rien à fermer
        return
    for ctx in list(br.contexts):
        try:
            ctx.close()
        except Exception:        # déjà fermé par le test, ou navigateur parti : rien à faire
            pass
