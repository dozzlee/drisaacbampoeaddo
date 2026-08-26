(function(){
  "use strict";

  var FORM_URL = "https://forms.gle/51uhbtPHeEK7PiHK6";
  var HERO_HEADER_IMAGE = "web-pictures/headerfinal.png";
  var galleryFiles = Array.isArray(window.TRIBUTE_PICTURES) ? window.TRIBUTE_PICTURES.slice() : [
    HERO_HEADER_IMAGE,
    "web-pictures/photo.jpeg",
    "web-pictures/gallery-001.jpg"
  ];
  var portraitGalleryFiles = Array.isArray(window.TRIBUTE_PORTRAIT_PICTURES)
    ? window.TRIBUTE_PORTRAIT_PICTURES.slice()
    : galleryFiles.slice();

  function shuffle(arr){
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function isPresidentPhoto(src){
    var filename = src.split("/").pop().toLowerCase();
    return /^(?:pre(?:s|z)|oresz)/.test(filename);
  }

  function prioritizePhotos(files){
    var presidentPhotos = files.filter(isPresidentPhoto);
    var remainingPhotos = files.filter(function(src){ return !isPresidentPhoto(src); });
    return shuffle(presidentPhotos).concat(shuffle(remainingPhotos));
  }

  var featuredGalleryFiles = [
    "web-pictures/IMG_0825.jpg",
    "web-pictures/IMG_0824.jpg",
    "web-pictures/IMG_0823.jpg",
    "web-pictures/IMG_0822.jpg",
    "web-pictures/IMG_0821.jpg",
    "web-pictures/IMG_0819.jpg",
    "web-pictures/IMG_0818.jpg",
    "web-pictures/IMG_0817.jpg",
    "web-pictures/IMG_0816.jpg",
    "web-pictures/IMG_0815.jpg",
    "web-pictures/IMG_0813.jpg",
    "web-pictures/IMG_0812.jpg",
    "web-pictures/IMG_0809.jpg",
    "web-pictures/IMG_0805.jpg",
    "web-pictures/IMG_0801.jpg",
    "web-pictures/IMG_0800.jpg",
    "web-pictures/IMG_0799.jpg",
    "web-pictures/IMG_0798.jpg",
    "web-pictures/IMG_0796.jpg",
    "web-pictures/cd45616d-83c0-4f92-b4a1-d3568850f630.JPG"
  ].filter(function(src){ return galleryFiles.indexOf(src) !== -1; });
  var featuredGallerySet = new Set(featuredGalleryFiles);
  var randomizedGallery = featuredGalleryFiles.concat(shuffle(galleryFiles.filter(function(src){
    return !featuredGallerySet.has(src);
  })));

  /* ---------------- Remembrance service announcement ---------------- */
  var eventModal = document.getElementById("eventModal");
  var eventModalClose = document.getElementById("eventModalClose");
  var eventFlyerTrack = document.getElementById("eventFlyerTrack");
  var eventFlyerDots = document.getElementById("eventFlyerDots");
  var eventFlyerIndex = 0;
  var eventFlyerCount = eventFlyerTrack ? eventFlyerTrack.children.length : 0;
  var eventFlyerTimer;
  var eventCountdownTimer;
  var eventTarget = new Date("2026-08-28T08:30:00Z").getTime();
  var lastFocusedElement = document.activeElement;

  function showEventFlyer(index){
    if (!eventFlyerCount) return;
    eventFlyerIndex = (index + eventFlyerCount) % eventFlyerCount;
    eventFlyerTrack.style.transform = "translateX(-" + (eventFlyerIndex * 100) + "%)";
    eventFlyerDots.querySelectorAll("button").forEach(function(dot, dotIndex){
      dot.classList.toggle("active", dotIndex === eventFlyerIndex);
      dot.setAttribute("aria-current", dotIndex === eventFlyerIndex ? "true" : "false");
    });
  }

  function restartEventFlyerTimer(){
    clearInterval(eventFlyerTimer);
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
      eventFlyerTimer = setInterval(function(){ showEventFlyer(eventFlyerIndex + 1); }, 5500);
    }
  }

  function closeEventModal(){
    eventModal.hidden = true;
    document.body.classList.remove("event-modal-open");
    clearInterval(eventFlyerTimer);
    clearInterval(eventCountdownTimer);
    window.dispatchEvent(new CustomEvent("memorial:event-closed"));
    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") lastFocusedElement.focus();
  }

  function setCountdownValue(id, value){
    document.getElementById(id).textContent = String(Math.max(0, value)).padStart(2, "0");
  }

  function updateEventCountdown(){
    var remaining = Math.max(0, eventTarget - Date.now());
    var totalSeconds = Math.floor(remaining / 1000);
    var days = Math.floor(totalSeconds / 86400);
    var hours = Math.floor((totalSeconds % 86400) / 3600);
    var minutes = Math.floor((totalSeconds % 3600) / 60);
    var seconds = totalSeconds % 60;
    setCountdownValue("countdownDays", days);
    setCountdownValue("countdownHours", hours);
    setCountdownValue("countdownMinutes", minutes);
    setCountdownValue("countdownSeconds", seconds);
    if (!remaining) clearInterval(eventCountdownTimer);
  }

  if (eventModal){
    document.body.classList.add("event-modal-open");
    Array.from(eventFlyerTrack.children).forEach(function(_, index){
      var dot = document.createElement("button");
      dot.type = "button";
      dot.setAttribute("aria-label", "View flyer " + (index + 1));
      dot.addEventListener("click", function(){ showEventFlyer(index); restartEventFlyerTimer(); });
      eventFlyerDots.appendChild(dot);
    });
    document.getElementById("eventFlyerPrev").addEventListener("click", function(){ showEventFlyer(eventFlyerIndex - 1); restartEventFlyerTimer(); });
    document.getElementById("eventFlyerNext").addEventListener("click", function(){ showEventFlyer(eventFlyerIndex + 1); restartEventFlyerTimer(); });
    eventModalClose.addEventListener("click", closeEventModal);
    eventModal.querySelector("[data-event-close]").addEventListener("click", closeEventModal);
    document.addEventListener("keydown", function(event){
      if (event.key === "Escape" && !eventModal.hidden) closeEventModal();
    });
    showEventFlyer(0);
    restartEventFlyerTimer();
    updateEventCountdown();
    eventCountdownTimer = setInterval(updateEventCountdown, 1000);
    setTimeout(function(){ eventModalClose.focus(); }, 0);
  }

  /* ---------------- Header: scroll shadow + mobile menu ---------------- */
  var header = document.getElementById("siteHeader");
  window.addEventListener("scroll", function(){
    header.classList.toggle("scrolled", window.scrollY > 20);
  });
  var menuToggle = document.getElementById("menuToggle");
  var navLinks = document.getElementById("navLinks");
  function setMenu(open){
    navLinks.classList.toggle("open", open);
    menuToggle.setAttribute("aria-expanded", String(open));
    menuToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    document.body.classList.toggle("menu-open", open);
  }
  menuToggle.addEventListener("click", function(){
    setMenu(!navLinks.classList.contains("open"));
  });
  navLinks.querySelectorAll("a").forEach(function(a){
    a.addEventListener("click", function(){ setMenu(false); });
  });
  document.addEventListener("keydown", function(event){
    if (event.key === "Escape") setMenu(false);
  });

  /* ---------------- Reveal on scroll ---------------- */
  var revealEls = document.querySelectorAll(".reveal");
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if (entry.isIntersecting){ entry.target.classList.add("in"); io.unobserve(entry.target); }
    });
  }, { threshold: 0.15 });
  revealEls.forEach(function(el){ io.observe(el); });

  /* ---------------- Legacy image: alternate between two selected photographs ---------------- */
  var legacyImg = document.getElementById("legacyImage");
  if (legacyImg){
    var legacyImages = [
      "web-pictures/F18_5598.JPG",
      "web-pictures/F18_9952.JPG"
    ];
    var legacyIndex = 0;
    var reduceLegacyMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    legacyImg.src = legacyImages[legacyIndex];
    legacyImg.alt = "Dr Isaac Bampoe Addo";
    legacyImages.forEach(function(src){
      var preload = new Image();
      preload.src = src;
    });
    setInterval(function(){
      legacyIndex = (legacyIndex + 1) % legacyImages.length;
      if (reduceLegacyMotion){
        legacyImg.src = legacyImages[legacyIndex];
        return;
      }
      legacyImg.classList.add("is-switching");
      setTimeout(function(){
        legacyImg.src = legacyImages[legacyIndex];
        legacyImg.classList.remove("is-switching");
      }, 600);
    }, 7000);
  }

  /* ================= HERO BACKGROUND SLIDER ================= */
  /* Reuses two layers so the complete picture directory can crossfade efficiently. */
  var heroSlider = document.getElementById("heroBgSlider");
  if (heroSlider){
    var presidentGalleryFiles = galleryFiles.filter(isPresidentPhoto);
    var nonPresidentPortraits = portraitGalleryFiles.filter(function(src){
      return !isPresidentPhoto(src);
    });
    var heroCandidates = presidentGalleryFiles.concat(nonPresidentPortraits);
    var heroImages = [HERO_HEADER_IMAGE].concat(prioritizePhotos(heroCandidates.filter(function(src){
      return src !== HERO_HEADER_IMAGE;
    })));
    var heroControls = document.getElementById("heroSliderControls");
    var firstHeroLayer = heroSlider.querySelector(".hero-bg-slide");
    var secondHeroLayer = document.createElement("div");
    secondHeroLayer.className = "hero-bg-slide";
    heroSlider.appendChild(secondHeroLayer);
    var heroSlideEls = [firstHeroLayer, secondHeroLayer];
    var heroIndex = 0;
    var activeHeroLayer = 0;
    var heroTimer;
    var heroStartTimeout;

    function setHeroOrientation(layer, width, height){
      layer.classList.toggle("is-portrait", height > width);
      layer.classList.toggle("is-landscape", width >= height);
    }

    function prepareHeroLayer(layer, src, activate){
      var encodedSrc = encodeURI(src).replace(/"/g, "%22");
      var probe = new Image();
      layer.dataset.pendingSrc = src;
      probe.onload = function(){
        if (layer.dataset.pendingSrc !== src) return;
        setHeroOrientation(layer, probe.naturalWidth, probe.naturalHeight);
        layer.style.backgroundImage = 'url("' + encodedSrc + '")';
        if (activate) activate();
      };
      probe.onerror = function(){
        if (layer.dataset.pendingSrc !== src) return;
        layer.classList.remove("is-portrait", "is-landscape");
        layer.style.backgroundImage = 'url("' + encodedSrc + '")';
        if (activate) activate();
      };
      probe.src = src;
    }

    prepareHeroLayer(firstHeroLayer, heroImages[0]);

    function showHero(index){
      heroIndex = (index + heroImages.length) % heroImages.length;
      var nextLayer = activeHeroLayer === 0 ? 1 : 0;
      var previousLayer = activeHeroLayer;
      prepareHeroLayer(heroSlideEls[nextLayer], heroImages[heroIndex], function(){
        heroSlideEls[nextLayer].classList.add("active");
        heroSlideEls[previousLayer].classList.remove("active");
        activeHeroLayer = nextLayer;
      });
    }

    [
      { label: "Previous photograph", symbol: "‹", step: -1 },
      { label: "Next photograph", symbol: "›", step: 1 }
    ].forEach(function(control){
      var button = document.createElement("button");
      button.type = "button";
      button.setAttribute("aria-label", control.label);
      button.textContent = control.symbol;
      button.addEventListener("click", function(){
        showHero(heroIndex + control.step);
        restartHeroTimer();
      });
      heroControls.appendChild(button);
    });

    function startHeroTimer(initialDelay){
      clearTimeout(heroStartTimeout);
      clearInterval(heroTimer);
      if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
        if (initialDelay){
          heroStartTimeout = setTimeout(function(){
            showHero((heroIndex + 1) % heroImages.length);
            heroTimer = setInterval(function(){ showHero((heroIndex + 1) % heroImages.length); }, 7000);
          }, initialDelay);
        } else {
          heroTimer = setInterval(function(){ showHero((heroIndex + 1) % heroImages.length); }, 7000);
        }
      }
    }
    function restartHeroTimer(){ startHeroTimer(); }
    if (eventModal && !eventModal.hidden){
      window.addEventListener("memorial:event-closed", function(){ startHeroTimer(8000); }, { once: true });
    } else {
      startHeroTimer(8000);
    }
  }

  /* ================= TRIBUTES ================= */
  var tributes = Array.isArray(window.MEMORIAL_TRIBUTES) ? window.MEMORIAL_TRIBUTES : [];

  var tribSlides = document.getElementById("tributeSlides");
  var tribDotsWrap = document.getElementById("tribDots");

  function appendTributeCopy(container, tribute){
    var quoteMark = document.createElement("span");
    quoteMark.className = "quote-mark";
    quoteMark.setAttribute("aria-hidden", "true");
    quoteMark.innerHTML = "&ldquo;";
    container.appendChild(quoteMark);

    tribute.quote.forEach(function(paragraph){
      var quote = document.createElement("p");
      quote.className = "quote";
      quote.textContent = paragraph;
      container.appendChild(quote);
    });

    var name = document.createElement("div");
    name.className = "tribute-name";
    name.textContent = tribute.name;
    container.appendChild(name);

    if (tribute.rel){
      var relationship = document.createElement("div");
      relationship.className = "tribute-rel";
      relationship.textContent = tribute.rel;
      container.appendChild(relationship);
    }
  }

  function createTributeImage(tribute, loading){
    var imageWrap = document.createElement("div");
    imageWrap.className = "tribute-photo";
    var image = document.createElement("img");
    image.alt = tribute.imageAlt;
    image.loading = loading;
    image.decoding = "async";
    image.src = tribute.image;
    imageWrap.appendChild(image);
    return imageWrap;
  }

  tributes.forEach(function(t, idx){
    var slide = document.createElement("div");
    slide.className = "tribute-slide";
    var card = document.createElement("article");
    card.className = "tribute-card";
    card.appendChild(createTributeImage(t, idx === 0 ? "eager" : "lazy"));
    var copy = document.createElement("div");
    copy.className = "tribute-copy";
    appendTributeCopy(copy, t);
    card.appendChild(copy);
    slide.appendChild(card);
    tribSlides.appendChild(slide);

    var dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("aria-label", "View tribute " + (idx + 1));
    if (idx === 0) dot.classList.add("active");
    dot.addEventListener("click", function(){ goToTribute(idx); });
    tribDotsWrap.appendChild(dot);
  });

  var tribIndex = 0;
  var tribTotal = tributes.length;
  function renderTribute(){
    tribSlides.style.transform = "translateX(-" + (tribIndex * 100) + "%)";
    tribDotsWrap.querySelectorAll("button").forEach(function(d, i){
      d.classList.toggle("active", i === tribIndex);
    });
  }
  function goToTribute(i){ tribIndex = (i + tribTotal) % tribTotal; renderTribute(); resetTribAuto(); }
  document.getElementById("tribPrev").addEventListener("click", function(){ goToTribute(tribIndex - 1); });
  document.getElementById("tribNext").addEventListener("click", function(){ goToTribute(tribIndex + 1); });

  var tribAuto;
  var tribHoldActive = false;
  function startTribAuto(){
    if (!tribHoldActive && !window.matchMedia("(prefers-reduced-motion: reduce)").matches){
      tribAuto = setInterval(function(){ goToTribute(tribIndex + 1); }, 50000);
    }
  }
  function resetTribAuto(){ clearInterval(tribAuto); startTribAuto(); }
  function pauseTributes(){
    tribHoldActive = true;
    clearInterval(tribAuto);
    tribSlides.classList.add("is-held");
  }
  function resumeTributes(){
    if (!tribHoldActive) return;
    tribHoldActive = false;
    tribSlides.classList.remove("is-held");
    startTribAuto();
  }
  tribSlides.addEventListener("pointerdown", function(event){
    if (event.pointerType === "mouse" && event.button !== 0) return;
    pauseTributes();
    if (tribSlides.setPointerCapture) tribSlides.setPointerCapture(event.pointerId);
  });
  tribSlides.addEventListener("pointerup", resumeTributes);
  tribSlides.addEventListener("pointercancel", resumeTributes);
  tribSlides.addEventListener("lostpointercapture", resumeTributes);
  startTribAuto();
  renderTribute();

  /* ================= TIMELINE ================= */
  var timelineData = [
    { year: "March 2009", title: "National Treasurer, Civil Servants Association", text: "Earliest documented national leadership role, representing members in salary-arrears negotiations with government." },
    { year: "Early 2011", title: "Becomes Executive Secretary of CLOGSAG", text: "Assumes the association's top administrative office, a post he held for the next fifteen years." },
    { year: "September 2011", title: "Single Spine Migration", text: "Leads CLOGSAG's successful migration onto the Single Spine Salary Structure, jointly announced with the Ministry of Employment." },
    { year: "August 2013", title: "Pempamsie Hotel Inaugurated", text: "A 140-room hospitality centre in Cape Coast and CLOGSAG's flagship investment in income-generating assets." },
    { year: "March 2015", title: "CLOGSAG Fund Board Inaugurated", text: "Appointed to the 13-member board overseeing members' supplementary savings and lump-sum benefits." },
    { year: "July 2015", title: "Honorary Doctorate Conferred", text: "Awarded an honorary Doctor of Philosophy by the Technological University of the Americas for exemplary labour leadership." },
    { year: "2017", title: "Joins the Civil Service Council", text: "Appointed CLOGSAG's representative on the governing Civil Service Council, a role he held for years." },
    { year: "2018 – 2019", title: "Tier-2 Pension Breakthrough", text: "Confirms the transfer of outstanding Tier-2 pension contributions, closing a six-year national dispute." },
    { year: "October 2020", title: "Pempamsie Tier-3 Fund Launched", text: "A voluntary retirement savings product introduced with Hedge Pensions to help members save beyond the mandatory pension." },
    { year: "May 2022", title: "Neutrality Allowance Secured", text: "Ends a three-week nationwide strike after government agrees to pay the long-sought Neutrality Allowance." },
    { year: "September 2022", title: "Public Services Pensioners Association", text: "Inaugurates a new body to represent and advocate for retired public servants after they leave active service." },
    { year: "October 2023", title: "Pempamsie Housing Scheme", text: "Launches a pension-backed mortgage programme helping members finance or complete their primary residences." },
    { year: "July 2026", title: "Still in Service", text: "Presides over the election and swearing-in of CLOGSAG's newly elected executives, weeks before his passing." },
    { year: "21 August 2026", title: "Passes Away", text: "Dies after a brief illness while still serving as Executive Secretary of CLOGSAG and Chairman of the Forum of Public Sector Unions." }
  ];

  var tlWrap = document.getElementById("timelineList");
  timelineData.forEach(function(item, idx){
    var el = document.createElement("div");
    el.className = "tl-item reveal " + (idx % 2 === 0 ? "left" : "right");
    el.innerHTML =
      '<span class="tl-dot"></span>' +
      '<div class="tl-year">' + item.year + '</div>' +
      '<div class="tl-card"><h4>' + item.title + '</h4><p>' + item.text + '</p></div>';
    tlWrap.appendChild(el);
  });
  document.querySelectorAll(".tl-item.reveal").forEach(function(el){ io.observe(el); });

  /* ================= GALLERY SLIDER (fully randomized on every page load) ================= */
  var galTrack = document.querySelector(".gallery-track");
  var galSlides = document.getElementById("gallerySlides");
  var GAL_GAP = 24;
  randomizedGallery.forEach(function(src, idx){
    var slide = document.createElement("div");
    slide.className = "gallery-slide";
    var img = document.createElement("img");
    img.alt = "Dr Isaac Bampoe Addo, photo memory";
    img.loading = idx < 10 ? "eager" : "lazy";
    img.decoding = "async";
    if (idx < 4) img.fetchPriority = "high";
    img.addEventListener("load", function(){
      if (!img.naturalWidth || !img.naturalHeight) return;
      slide.style.setProperty("--photo-ratio", img.naturalWidth + " / " + img.naturalHeight);
      slide.classList.toggle("is-landscape", img.naturalWidth > img.naturalHeight);
      slide.classList.toggle("is-portrait", img.naturalHeight >= img.naturalWidth);
      slide.classList.add("is-loaded");
    });
    img.src = src;
    slide.appendChild(img);
    galSlides.appendChild(slide);
  });

  var galSlideEls = galSlides.querySelectorAll(".gallery-slide");

  function preloadGalleryAround(index){
    for (var i = Math.max(0, index - 1); i <= Math.min(galSlideEls.length - 1, index + 7); i++){
      var image = galSlideEls[i].querySelector("img");
      if (image && !image.complete) image.loading = "eager";
    }
  }

  function currentGalleryIndex(){
    var step = galStep();
    return step ? Math.round(galTrack.scrollLeft / step) : 0;
  }

  function galStep(){
    return galSlideEls.length ? galSlideEls[0].getBoundingClientRect().width + GAL_GAP : 0;
  }
  function galAtEnd(){
    return galTrack.scrollLeft + galTrack.clientWidth >= galTrack.scrollWidth - 4;
  }
  document.getElementById("galPrev").addEventListener("click", function(){
    preloadGalleryAround(Math.max(0, currentGalleryIndex() - 1));
    galTrack.scrollBy({ left: -galStep(), behavior: "smooth" });
  });
  document.getElementById("galNext").addEventListener("click", function(){
    var nextIndex = galAtEnd() ? 0 : currentGalleryIndex() + 1;
    preloadGalleryAround(nextIndex);
    if (galAtEnd()) galTrack.scrollTo({ left: 0, behavior: "smooth" });
    else galTrack.scrollBy({ left: galStep(), behavior: "smooth" });
  });

  var galleryPreloadFrame;
  galTrack.addEventListener("scroll", function(){
    cancelAnimationFrame(galleryPreloadFrame);
    galleryPreloadFrame = requestAnimationFrame(function(){
      preloadGalleryAround(currentGalleryIndex());
    });
  }, { passive: true });

  preloadGalleryAround(0);

  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
    setInterval(function(){
      var nextIndex = galAtEnd() ? 0 : currentGalleryIndex() + 1;
      preloadGalleryAround(nextIndex);
      if (galAtEnd()) galTrack.scrollTo({ left: 0, behavior: "smooth" });
      else galTrack.scrollBy({ left: galStep(), behavior: "smooth" });
    }, 4200);
  }

})();
