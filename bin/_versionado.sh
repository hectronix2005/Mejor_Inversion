# shellcheck shell=bash
# Común a bin/etiquetar y bin/rollback.
# Las herramientas de versionado NO forman parte de una «versión»: un rollback trae el sitio de la
# etiqueta pero conserva estas rutas tal como están en main, y al comparar versiones se ignoran.
# shellcheck disable=SC2034  # se usa en bin/rollback
HERRAMIENTAS=(.github bin/sonda bin/etiquetar bin/rollback bin/_versionado.sh CLAUDE.md)
HERRAMIENTAS_RE=$'\t(\\.github/|bin/(sonda|etiquetar|rollback|_versionado\\.sh)$|CLAUDE\\.md$)'

# Huella del contenido del sitio de un commit/etiqueta (sin las herramientas).
huella() {
  git rev-parse -q --verify "$1^{tree}" >/dev/null 2>&1 || return 1
  git ls-tree -r "$1" | grep -vE "$HERRAMIENTAS_RE" | git hash-object --stdin
}
