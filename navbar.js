document.addEventListener("DOMContentLoaded", function(){

  const nav = document.getElementById("bottomNav");
  if(!nav) return;

  const indicator = document.getElementById("navIndicator");
  const links = nav.querySelectorAll(".nav-link");

  /* CENTER POSITION FIX */
  function getPosition(el){
    const navRect = nav.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();

    return (elRect.left - navRect.left) +
           (elRect.width / 2) -
           (indicator.offsetWidth / 2);
  }

  /* PAGE DETECT */
  let path = location.pathname.split("/").pop();

  if(path === "" || path === "/"){
    path = "index.html";
  }

  const currentPage = path;

  let activeLink = null;

  links.forEach(link=>{
    if(link.getAttribute("href") === currentPage){
      activeLink = link;
    }
  });

  /* INITIAL POSITION (DEPLOY FIX) */
  if(activeLink){

    requestAnimationFrame(()=>{
      requestAnimationFrame(()=>{

        indicator.style.transition = "none";

        indicator.style.transform =
          `translateX(${getPosition(activeLink)}px)`;

        activeLink.classList.add("active");

        setTimeout(()=>{
          indicator.style.transition =
            "transform 0.55s cubic-bezier(.34,1.56,.64,1)";
        },50);

      });
    });
  }

  /* CLICK ANIMATION */
  links.forEach(link=>{
    link.addEventListener("click", function(e){

      if(this.getAttribute("href") === currentPage){
        return;
      }

      e.preventDefault();

      let newX = getPosition(this);

      indicator.style.transform =
        `translateX(${newX}px)`;

      links.forEach(l=>l.classList.remove("active"));
      this.classList.add("active");

      setTimeout(()=>{
        window.location.href =
          this.getAttribute("href");
      },400);

    });
  });

  /* RESIZE FIX */
  window.addEventListener("resize", ()=>{
    if(activeLink){
      setTimeout(()=>{
        indicator.style.transform =
          `translateX(${getPosition(activeLink)}px)`;
      },100);
    }
  });

});