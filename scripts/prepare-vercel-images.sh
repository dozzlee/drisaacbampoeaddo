#!/bin/zsh
set -euo pipefail

project_root="${0:A:h:h}"
source_root="$project_root/pictures"
output_root="$project_root/web-pictures"

if ! command -v sips >/dev/null 2>&1; then
  print -u2 "This image preparation script requires macOS sips."
  exit 1
fi

mkdir -p "$output_root"

find "$source_root" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0 |
while IFS= read -r -d '' source_file; do
  relative_path="${source_file#$source_root/}"
  output_file="$output_root/$relative_path"
  mkdir -p "${output_file:h}"

  case "${source_file:e:l}" in
    jpg|jpeg)
      sips -Z 960 -s format jpeg -s formatOptions 40 "$source_file" --out "$output_file" >/dev/null
      ;;
    png)
      sips -Z 960 "$source_file" --out "$output_file" >/dev/null
      ;;
  esac
done

node "$project_root/scripts/generate-picture-manifest.mjs"
print "Prepared browser images in web-pictures and regenerated js/pictures.js."
