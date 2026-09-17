document.addEventListener("DOMContentLoaded", function () {

    const menuButton = document.getElementById("menuButton");
    const sidebar = document.getElementById("sidebar");



    /* ==========================================
       MOBILE MENU
    ========================================== */

    if (menuButton && sidebar) {

        menuButton.addEventListener("click", function () {

            sidebar.classList.toggle("active");

        });

    }



    /* ==========================================
       CLOSE SIDEBAR WHEN CLICKING OUTSIDE
    ========================================== */

    document.addEventListener("click", function (event) {

        if (!sidebar || !menuButton) {
            return;
        }


        const clickedInsideSidebar =
            sidebar.contains(event.target);

        const clickedMenuButton =
            menuButton.contains(event.target);


        if (
            window.innerWidth <= 768 &&
            !clickedInsideSidebar &&
            !clickedMenuButton &&
            sidebar.classList.contains("active")
        ) {

            sidebar.classList.remove("active");

        }

    });



    /* ==========================================
       CLOSE SIDEBAR AFTER CLICKING A LINK
    ========================================== */

    const sidebarLinks =
        document.querySelectorAll(".sidebar .nav-link");


    sidebarLinks.forEach(function (link) {

        link.addEventListener("click", function () {

            if (window.innerWidth <= 768) {

                sidebar.classList.remove("active");

            }

        });

    });



    /* ==========================================
       HANDLE SCREEN RESIZE
    ========================================== */

    window.addEventListener("resize", function () {

        if (window.innerWidth > 768) {

            sidebar.classList.remove("active");

        }

    });

});