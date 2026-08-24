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

find "$source_root" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.nef' \) -print0 |
while IFS= read -r -d '' source_file; do
  relative_path="${source_file#$source_root/}"
  source_extension="${source_file:e:l}"

  if [[ "$source_extension" == "nef" ]]; then
    source_stem="${source_file:r}"
    has_rendered_sibling=false
    for sibling_extension in JPG jpg JPEG jpeg PNG png; do
      if [[ -f "$source_stem.$sibling_extension" ]]; then
        has_rendered_sibling=true
        break
      fi
    done
    if [[ "$has_rendered_sibling" == true ]]; then
      continue
    fi
    output_file="$output_root/${relative_path:r}.jpg"
  else
    output_file="$output_root/$relative_path"
  fi

  mkdir -p "${output_file:h}"

  if [[ -f "$output_file" && ! "$source_file" -nt "$output_file" ]]; then
    continue
  fi

  case "$source_extension" in
    jpg|jpeg|nef)
      sips -Z 960 -s format jpeg -s formatOptions 40 "$source_file" --out "$output_file" >/dev/null
      ;;
    png)
      sips -Z 960 "$source_file" --out "$output_file" >/dev/null
      ;;
  esac
done

# Keep the deploy-ready directory aligned with the current source archive.
find "$output_root" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0 |
while IFS= read -r -d '' output_file; do
  relative_path="${output_file#$output_root/}"
  has_source=false
  if [[ -f "$source_root/$relative_path" ]]; then
    has_source=true
  elif [[ "${output_file:e:l}" == "jpg" || "${output_file:e:l}" == "jpeg" ]]; then
    source_stem="$source_root/${relative_path:r}"
    if [[ -f "$source_stem.NEF" || -f "$source_stem.nef" ]]; then
      has_source=true
    fi
  fi

  if [[ "$has_source" == false ]]; then
    rm -f -- "$output_file"
  fi
done

find "$output_root" -depth -type d -empty -delete

node "$project_root/scripts/generate-picture-manifest.mjs"
print "Prepared browser images in web-pictures and regenerated js/pictures.js."
