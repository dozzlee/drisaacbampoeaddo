(function(){
  "use strict";

  var tributes = Array.isArray(window.MEMORIAL_TRIBUTES) ? window.MEMORIAL_TRIBUTES : [];
  var library = document.getElementById("tributeLibrary");
  var reader = document.getElementById("tributeReader");
  var readerClose = document.getElementById("tributeReaderClose");
  var readerPhoto = document.getElementById("tributeReaderPhoto");
  var readerQuote = document.getElementById("tributeReaderQuote");
  var readerName = document.getElementById("tributeReaderName");
  var readerRel = document.getElementById("tributeReaderRel");
  var lastFocusedElement;

  function addQuoteParagraphs(container, paragraphs){
    container.replaceChildren();
    paragraphs.forEach(function(paragraph){
      var text = document.createElement("p");
      text.textContent = paragraph;
      container.appendChild(text);
    });
  }

  function openTribute(tribute, updateHash){
    lastFocusedElement = document.activeElement;
    var image = document.createElement("img");
    image.src = tribute.image;
    image.alt = tribute.imageAlt;
    image.decoding = "async";
    readerPhoto.replaceChildren(image);
    addQuoteParagraphs(readerQuote, tribute.quote);
    readerName.textContent = tribute.name;
    readerRel.textContent = tribute.rel;
    readerRel.hidden = !tribute.rel;
    reader.hidden = false;
    document.body.classList.add("tribute-reader-open");
    if (updateHash) history.replaceState(null, "", "#" + tribute.slug);
    readerClose.focus();
  }

  function closeTribute(updateHash){
    reader.hidden = true;
    document.body.classList.remove("tribute-reader-open");
    if (updateHash) history.replaceState(null, "", window.location.pathname + window.location.search);
    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") lastFocusedElement.focus();
  }

  tributes.forEach(function(tribute, index){
    var card = document.createElement("a");
    card.className = "tribute-library-card";
    card.href = "tributes.html#" + tribute.slug;

    var imageWrap = document.createElement("div");
    imageWrap.className = "tribute-library-photo";
    var image = document.createElement("img");
    image.src = tribute.image;
    image.alt = tribute.imageAlt;
    image.loading = index < 4 ? "eager" : "lazy";
    image.decoding = "async";
    imageWrap.appendChild(image);

    var copy = document.createElement("div");
    copy.className = "tribute-library-copy";
    var mark = document.createElement("span");
    mark.className = "quote-mark";
    mark.setAttribute("aria-hidden", "true");
    mark.innerHTML = "&ldquo;";
    var excerpt = document.createElement("p");
    excerpt.textContent = tribute.quote[0];
    var name = document.createElement("h2");
    name.textContent = tribute.name;
    var instruction = document.createElement("span");
    instruction.className = "tribute-library-read";
    instruction.textContent = "Read Full Tribute";
    copy.append(mark, excerpt, name, instruction);
    card.append(imageWrap, copy);
    card.addEventListener("click", function(event){
      event.preventDefault();
      openTribute(tribute, true);
    });
    library.appendChild(card);
  });

  readerClose.addEventListener("click", function(){ closeTribute(true); });
  reader.querySelector("[data-reader-close]").addEventListener("click", function(){ closeTribute(true); });
  document.addEventListener("keydown", function(event){
    if (event.key === "Escape" && !reader.hidden) closeTribute(true);
  });

  var requestedSlug = window.location.hash.slice(1);
  if (requestedSlug){
    var requestedTribute = tributes.find(function(tribute){ return tribute.slug === requestedSlug; });
    if (requestedTribute) openTribute(requestedTribute, false);
  }
})();
