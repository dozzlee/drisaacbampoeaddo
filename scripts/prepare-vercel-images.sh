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

find "$source_root" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.nef' -o -iname '*.heic' -o -iname '*.heif' \) -print0 |
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
  elif [[ "$source_extension" == "heic" || "$source_extension" == "heif" ]]; then
    output_file="$output_root/${relative_path:r}.jpg"
  else
    output_file="$output_root/$relative_path"
  fi

  mkdir -p "${output_file:h}"

  if [[ -f "$output_file" && ! "$source_file" -nt "$output_file" && "$source_extension" != "nef" && "$source_extension" != "heic" && "$source_extension" != "heif" && "$relative_path" != "tribute-nanayaw-01.jpeg" ]]; then
    continue
  fi

  case "$source_extension" in
    nef|heic|heif)
      preview_dir="$(mktemp -d)"
      qlmanage -t -s 1200 -o "$preview_dir" "$source_file" >/dev/null
      preview_file="$preview_dir/${source_file:t}.png"
      if [[ ! -f "$preview_file" ]]; then
        print -u2 "Quick Look could not prepare $source_file"
        rm -rf -- "$preview_dir"
        exit 1
      fi
      sips -Z 960 -s format jpeg -s formatOptions 48 "$preview_file" --out "$output_file" >/dev/null
      rm -rf -- "$preview_dir"
      ;;
    jpg|jpeg)
      if [[ "$relative_path" == "tribute-nanayaw-01.jpeg" ]]; then
        preview_dir="$(mktemp -d)"
        qlmanage -t -s 1200 -o "$preview_dir" "$source_file" >/dev/null
        preview_file="$preview_dir/${source_file:t}.png"
        sips -Z 960 -s format jpeg -s formatOptions 48 "$preview_file" --out "$output_file" >/dev/null
        rm -rf -- "$preview_dir"
      else
        sips -Z 960 -s format jpeg -s formatOptions 40 "$source_file" --out "$output_file" >/dev/null
      fi
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
    if [[ -f "$source_stem.NEF" || -f "$source_stem.nef" || -f "$source_stem.HEIC" || -f "$source_stem.heic" || -f "$source_stem.HEIF" || -f "$source_stem.heif" ]]; then
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
