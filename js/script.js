(function(){
  "use strict";

  var FORM_URL = "https://forms.gle/51uhbtPHeEK7PiHK6";
  var galleryFiles = Array.isArray(window.TRIBUTE_PICTURES) ? window.TRIBUTE_PICTURES.slice() : [
    "web-pictures/header.png",
    "web-pictures/photo.jpeg",
    "web-pictures/gallery-001.jpg"
  ];

  function shuffle(arr){
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  var shuffledGallery = shuffle(galleryFiles);

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

  /* ---------------- Legacy image: randomize on load ---------------- */
  var legacyImg = document.getElementById("legacyImage");
  if (legacyImg){
    var randomPick = galleryFiles[Math.floor(Math.random() * galleryFiles.length)];
    legacyImg.src = randomPick;
    legacyImg.alt = "Dr Isaac Bampoe Addo";
  }

  /* ================= HERO BACKGROUND SLIDER ================= */
  /* Reuses two layers so the complete picture directory can crossfade efficiently. */
  var heroSlider = document.getElementById("heroBgSlider");
  if (heroSlider){
    var heroImages = ["web-pictures/header.png"].concat(shuffle(galleryFiles.filter(function(src){
      return src !== "web-pictures/header.png";
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

    function startHeroTimer(){
      if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
        heroTimer = setInterval(function(){ showHero((heroIndex + 1) % heroImages.length); }, 7000);
      }
    }
    function restartHeroTimer(){ clearInterval(heroTimer); startHeroTimer(); }
    startHeroTimer();
  }

  /* ================= TRIBUTES (filler content) ================= */
  var tributes = [
    {
      quote: "Dr Bampoe Addo fought for every one of us. Because of him, my Tier-2 pension is finally in the hands of people who actually care about workers.",
      name: "A Grateful CLOGSAG Member",
      rel: "Local Government Service, Ashanti Region"
    },
    {
      quote: "He picked up the phone at any hour if a member had a problem. Losing him feels like losing a father to this entire association.",
      name: "A Civil Servant Colleague",
      rel: "Office of the Head of the Civil Service"
    },
    {
      quote: "Sir never backed down from a fight he believed was right for us. The Neutrality Allowance would not exist without his persistence.",
      name: "A Regional Union Officer",
      rel: "CLOGSAG, Northern Region"
    },
    {
      quote: "He believed our welfare didn't end at retirement. The Pensioners Association he built continues to change lives today.",
      name: "A Retired Public Servant",
      rel: "Public Services Pensioners Association"
    },
    {
      quote: "A brilliant negotiator, but above all a kind and humble man who always remembered your name.",
      name: "A Friend & Fellow Unionist",
      rel: "Forum of Public Sector Unions"
    },
    {
      quote: "Dad taught us that service to others is the truest measure of a life well lived. We will carry his legacy forward.",
      name: "The Bampoe Addo Family",
      rel: "In Loving Memory"
    }
  ];

  var tribSlides = document.getElementById("tributeSlides");
  var tribDotsWrap = document.getElementById("tribDots");
  tributes.forEach(function(t, idx){
    var slide = document.createElement("div");
    slide.className = "tribute-slide";
    slide.innerHTML =
      '<div class="tribute-card">' +
        '<span class="quote-mark">&ldquo;</span>' +
        '<p class="quote">' + t.quote + '</p>' +
        '<div class="tribute-name">' + t.name + '</div>' +
        '<div class="tribute-rel">' + t.rel + '</div>' +
      '</div>';
    tribSlides.appendChild(slide);

    var dot = document.createElement("button");
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
  function startTribAuto(){
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
      tribAuto = setInterval(function(){ goToTribute(tribIndex + 1); }, 6000);
    }
  }
  function resetTribAuto(){ clearInterval(tribAuto); startTribAuto(); }
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

  /* ================= GALLERY SLIDER (large tiles, randomized order, native scroll) ================= */
  var galTrack = document.querySelector(".gallery-track");
  var galSlides = document.getElementById("gallerySlides");
  var GAL_GAP = 24;
  shuffledGallery.forEach(function(src){
    var slide = document.createElement("div");
    slide.className = "gallery-slide";
    var img = document.createElement("img");
    img.alt = "Dr Isaac Bampoe Addo, photo memory";
    img.loading = "lazy";
    img.addEventListener("load", function(){
      if (!img.naturalWidth || !img.naturalHeight) return;
      slide.style.setProperty("--photo-ratio", img.naturalWidth + " / " + img.naturalHeight);
      slide.classList.toggle("is-landscape", img.naturalWidth > img.naturalHeight);
      slide.classList.toggle("is-portrait", img.naturalHeight >= img.naturalWidth);
    });
    img.src = src;
    slide.appendChild(img);
    galSlides.appendChild(slide);
  });

  var galSlideEls = galSlides.querySelectorAll(".gallery-slide");

  function galStep(){
    return galSlideEls.length ? galSlideEls[0].getBoundingClientRect().width + GAL_GAP : 0;
  }
  function galAtEnd(){
    return galTrack.scrollLeft + galTrack.clientWidth >= galTrack.scrollWidth - 4;
  }
  document.getElementById("galPrev").addEventListener("click", function(){
    galTrack.scrollBy({ left: -galStep(), behavior: "smooth" });
  });
  document.getElementById("galNext").addEventListener("click", function(){
    if (galAtEnd()){ galTrack.scrollTo({ left: 0, behavior: "smooth" }); }
    else{ galTrack.scrollBy({ left: galStep(), behavior: "smooth" }); }
  });

  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
    setInterval(function(){
      if (galAtEnd()){ galTrack.scrollTo({ left: 0, behavior: "smooth" }); }
      else{ galTrack.scrollBy({ left: galStep(), behavior: "smooth" }); }
    }, 4200);
  }

})();
