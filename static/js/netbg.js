/* Connected-dots background (GNT Partners). Draws behind page content. */
(function () {
    var cv = document.getElementById("netbg");
    if (!cv || !cv.getContext) return;
    var st = document.createElement("style");
    st.textContent = "#netbg{position:fixed;inset:0;width:100%;height:100%;z-index:0;pointer-events:none}";
    document.head.appendChild(st);
    var cx = cv.getContext("2d"), W = 0, H = 0, pts = [];
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

    function size() {
        W = window.innerWidth; H = window.innerHeight;
        cv.width = W * dpr; cv.height = H * dpr;
        cx.setTransform(dpr, 0, 0, dpr, 0, 0);
        var n = Math.round(Math.min(70, (W * H) / 26000));
        pts = [];
        for (var i = 0; i < n; i++) {
            pts.push({ x: Math.random() * W, y: Math.random() * H,
                       vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3 });
        }
    }

    function frame() {
        cx.clearRect(0, 0, W, H);
        for (var i = 0; i < pts.length; i++) {
            var a = pts[i];
            if (!reduce) {
                a.x += a.vx; a.y += a.vy;
                if (a.x < 0 || a.x > W) a.vx *= -1;
                if (a.y < 0 || a.y > H) a.vy *= -1;
            }
            for (var j = i + 1; j < pts.length; j++) {
                var b = pts[j], dx = a.x - b.x, dy = a.y - b.y, d = Math.sqrt(dx * dx + dy * dy);
                if (d < 150) {
                    cx.strokeStyle = "rgba(37,99,235," + (0.18 * (1 - d / 150)) + ")";
                    cx.lineWidth = 1;
                    cx.beginPath(); cx.moveTo(a.x, a.y); cx.lineTo(b.x, b.y); cx.stroke();
                }
            }
            cx.fillStyle = "rgba(37,99,235,.35)";
            cx.beginPath(); cx.arc(a.x, a.y, 2, 0, 6.3); cx.fill();
        }
        if (!reduce && !document.hidden) requestAnimationFrame(frame);
    }

    document.addEventListener("visibilitychange", function () { if (!document.hidden && !reduce) requestAnimationFrame(frame); });
    window.addEventListener("resize", function () { size(); if (reduce) frame(); });
    size(); frame();
})();
