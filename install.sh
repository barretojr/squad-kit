#!/usr/bin/env bash
# Installs the Squad for Antigravity (.agents/ in a project, or ~/.gemini/config globally).
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$script_dir/squad-kit"
kinds=(agents rules skills commands mcp)

if [[ ! -d "$source_dir" ]]; then
  echo "Error: source folder squad-kit not found in $script_dir" >&2
  exit 1
fi

copy_squad_to() {
  local destination_root="$1"
  mkdir -p "$destination_root"
  for kind in "${kinds[@]}"; do
    if [[ -d "$source_dir/$kind" ]]; then
      mkdir -p "$destination_root/$kind"
      cp -R "$source_dir/$kind/." "$destination_root/$kind/"
    fi
  done
  # The squad skill reads its rules from references/rules.md
  cp "$source_dir/rules/squad-context.md" "$destination_root/skills/squad/references/rules.md"
}

install_global() {
  local config_dir="$HOME/.gemini/config"
  copy_squad_to "$config_dir"
  local global_skills_dir="$HOME/.gemini/antigravity-cli/skills"
  mkdir -p "$global_skills_dir"
  cp -R "$source_dir/skills/." "$global_skills_dir/"
  cp "$source_dir/rules/squad-context.md" "$global_skills_dir/squad/references/rules.md"
  echo "Squad and skills installed globally in $config_dir and $global_skills_dir"
  echo "MCP server: python3 '$config_dir/mcp/server.py' (stdio)"
}

if [[ "${1:-}" == "--global" || "${1:-}" == "-g" ]]; then
  install_global
  exit 0
fi

target_project="${1:-}"
if [[ -z "$target_project" ]]; then
  echo "1) Install into the current folder ($(pwd))"
  echo "2) Enter another project"
  echo "3) Install globally"
  echo "q) Cancel"
  read -rp "Option: " choice
  case "$choice" in
    1) target_project="$(pwd)" ;;
    2) read -rp "Project root: " target_project ;;
    3) install_global; exit 0 ;;
    *) echo "Cancelled."; exit 0 ;;
  esac
fi

if [[ ! -d "$target_project" ]]; then
  echo "Project folder not found: $target_project" >&2
  exit 1
fi
copy_squad_to "$target_project/.agents"

# Make sure .squad/ is in the project's .gitignore
gitignore_path="$target_project/.gitignore"
if [[ ! -f "$gitignore_path" ]] || ! grep -qE '^\.squad/?\s*$' "$gitignore_path"; then
  printf "\n# Squad artifacts\n.squad/\n" >> "$gitignore_path"
  echo "Added .squad/ to $gitignore_path"
fi

echo "Squad installed in the workspace: $target_project/.agents"
echo "Reopen or reload Antigravity and run /squad."
echo "MCP server: python3 '$target_project/.agents/mcp/server.py' (stdio)"
