(function(){
  "use strict";

  var tributes = Array.isArray(window.MEMORIAL_TRIBUTES) ? window.MEMORIAL_TRIBUTES : [];
  var library = document.getElementById("tributeLibrary");
  var reader = document.getElementById("tributeReader");
  var readerPanel = reader ? reader.querySelector(".tribute-reader-panel") : null;
  var readerClose = document.getElementById("tributeReaderClose");
  var readerPrev = document.getElementById("tributeReaderPrev");
  var readerNext = document.getElementById("tributeReaderNext");
  var readerPhoto = document.getElementById("tributeReaderPhoto");
  var readerQuote = document.getElementById("tributeReaderQuote");
  var readerName = document.getElementById("tributeReaderName");
  var readerRel = document.getElementById("tributeReaderRel");
  var lastFocusedElement;

  var currentTributeIndex = 0;
  var autoSlideTimer = null;
  var isHoldActive = false;
  var AUTO_INTERVAL = 50000; // 50 seconds

  function addQuoteParagraphs(container, paragraphs){
    container.replaceChildren();
    paragraphs.forEach(function(paragraph){
      var text = document.createElement("p");
      text.textContent = paragraph;
      container.appendChild(text);
    });
  }

  function startAutoSlide(){
    clearInterval(autoSlideTimer);
    if (!reader || reader.hidden || isHoldActive || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    autoSlideTimer = setInterval(function(){
      goToNextTribute();
    }, AUTO_INTERVAL);
  }

  function stopAutoSlide(){
    clearInterval(autoSlideTimer);
  }

  function restartAutoSlide(){
    stopAutoSlide();
    startAutoSlide();
  }

  function pauseAutoSlide(){
    isHoldActive = true;
    stopAutoSlide();
  }

  function resumeAutoSlide(){
    if (!isHoldActive) return;
    isHoldActive = false;
    startAutoSlide();
  }

  function renderCurrentTribute(updateHash){
    var tribute = tributes[currentTributeIndex];
    if (!tribute) return;

    var image = document.createElement("img");
    image.src = tribute.image;
    image.alt = tribute.imageAlt;
    image.decoding = "async";
    readerPhoto.replaceChildren(image);

    addQuoteParagraphs(readerQuote, tribute.quote);
    readerName.textContent = tribute.name;
    readerRel.textContent = tribute.rel;
    readerRel.hidden = !tribute.rel;

    var panel = reader.querySelector(".tribute-reader-panel");
    if (panel) panel.scrollTop = 0;
    var copy = reader.querySelector(".tribute-reader-copy");
    if (copy) copy.scrollTop = 0;
    reader.scrollTop = 0;

    if (updateHash) history.replaceState(null, "", "#" + tribute.slug);
  }

  function openTributeByIndex(index, updateHash){
    lastFocusedElement = document.activeElement;
    currentTributeIndex = (index + tributes.length) % tributes.length;
    renderCurrentTribute(updateHash);
    reader.hidden = false;
    document.body.classList.add("tribute-reader-open");
    restartAutoSlide();
    if (typeof readerClose.focus === "function") {
      try {
        readerClose.focus({ preventScroll: true });
      } catch (e) {
        readerClose.focus();
      }
    }
  }

  function closeTribute(updateHash){
    reader.hidden = true;
    document.body.classList.remove("tribute-reader-open");
    stopAutoSlide();
    isHoldActive = false;
    if (updateHash) history.replaceState(null, "", window.location.pathname + window.location.search);
    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") lastFocusedElement.focus();
  }

  function goToNextTribute(){
    if (!tributes.length) return;
    currentTributeIndex = (currentTributeIndex + 1) % tributes.length;
    renderCurrentTribute(true);
    restartAutoSlide();
  }

  function goToPrevTribute(){
    if (!tributes.length) return;
    currentTributeIndex = (currentTributeIndex - 1 + tributes.length) % tributes.length;
    renderCurrentTribute(true);
    restartAutoSlide();
  }

  // Populate library cards
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
      openTributeByIndex(index, true);
    });
    library.appendChild(card);
  });

  // Close handlers
  readerClose.addEventListener("click", function(){ closeTribute(true); });
  reader.querySelector("[data-reader-close]").addEventListener("click", function(){ closeTribute(true); });

  // Navigation handlers
  if (readerPrev) readerPrev.addEventListener("click", function(e){ e.stopPropagation(); goToPrevTribute(); });
  if (readerNext) readerNext.addEventListener("click", function(e){ e.stopPropagation(); goToNextTribute(); });

  // Keyboard navigation
  document.addEventListener("keydown", function(event){
    if (reader.hidden) return;
    if (event.key === "Escape") closeTribute(true);
    else if (event.key === "ArrowRight") goToNextTribute();
    else if (event.key === "ArrowLeft") goToPrevTribute();
  });

  // Press & hold to pause on tribute panel
  if (readerPanel){
    readerPanel.addEventListener("pointerdown", function(event){
      if (event.pointerType === "mouse" && event.button !== 0) return;
      pauseAutoSlide();
      if (readerPanel.setPointerCapture) {
        try { readerPanel.setPointerCapture(event.pointerId); } catch(e){}
      }
    });
    readerPanel.addEventListener("pointerup", resumeAutoSlide);
    readerPanel.addEventListener("pointercancel", resumeAutoSlide);
    readerPanel.addEventListener("lostpointercapture", resumeAutoSlide);
  }

  // Mobile horizontal swipe gestures (without breaking vertical scroll)
  var touchStartX = 0;
  var touchStartY = 0;
  var touchStartTime = 0;

  reader.addEventListener("touchstart", function(event){
    if (event.touches.length === 1){
      touchStartX = event.touches[0].clientX;
      touchStartY = event.touches[0].clientY;
      touchStartTime = Date.now();
    }
  }, { passive: true });

  reader.addEventListener("touchend", function(event){
    if (event.changedTouches.length === 1){
      var touchEndX = event.changedTouches[0].clientX;
      var touchEndY = event.changedTouches[0].clientY;
      var deltaX = touchEndX - touchStartX;
      var deltaY = touchEndY - touchStartY;
      var elapsed = Date.now() - touchStartTime;

      if (Math.abs(deltaX) > 40 && Math.abs(deltaX) > Math.abs(deltaY) * 1.25 && elapsed < 800){
        if (deltaX < 0){
          goToNextTribute();
        } else {
          goToPrevTribute();
        }
      }
    }
  }, { passive: true });

  // Open from URL hash if present
  var requestedSlug = window.location.hash.slice(1);
  if (requestedSlug){
    var matchedIndex = tributes.findIndex(function(tribute){ return tribute.slug === requestedSlug; });
    if (matchedIndex !== -1) openTributeByIndex(matchedIndex, false);
  }
})();
