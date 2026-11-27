"""La cohérence du dépôt, sans navigateur : le numéro de dev est le même partout où il est écrit. Ce test lit ces trois endroits et les compare ; il ne fige aucun numéro, aucun texte
d'un lot : un lot qui change `DEV_BUILD` (et reconstruit) passe sans toucher aucun test."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _lire(*chemin):
    return ROOT.joinpath(*chemin).read_text(encoding='utf-8')


def test_the_dev_build_number_is_the_same_in_the_code_the_changelog_and_the_home_screen():
    version = _lire('version_block.py')
    build = int(re.search(r'^DEV_BUILD = (\d+)$', version, re.M).group(1))
    suite = re.search(r'^SUITE_VERSION = [\'"]([^\'"]+)[\'"]', version, re.M).group(1)
    log = _lire('CHANGELOG.md')
    dites = re.findall(r'`MP-V' + re.escape(suite) + r'\+(\d+)` for this one', log)
    assert dites == [str(build)], (build, dites)                                        # la ligne « Build number on the hosted version » du CHANGELOG, une seule fois
    pied = re.search(r'<span id="foot-version" data-dev-build>MP-V' + re.escape(suite) + r'\+(\d+)</span>', _lire('dist', 'dcs_mission_plan.html'))
    assert pied and int(pied.group(1)) == build, (build, pied and pied.group(1))        # le numéro du pied de l'accueil construit


def test_the_changelog_has_its_unreleased_part_and_its_version_numbers_paragraph():
    log = _lire('CHANGELOG.md')
    assert log.count('\n## Unreleased\n') == 1
    assert log.count('\n### Version numbers\n') == 1
