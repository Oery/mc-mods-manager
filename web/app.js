eel.expose(addMod)
function addMod(mod) {
    const fragmentHTML = `
    <div class="mod">
        <div>
            <img src="{icon_path}" alt="Mod Icon" draggable="false">
            <h2>{name}</h2>
        </div>
        <div class="status">
            <p class="{status}">
                <span class="dot"></span></p>
        </div>
    </div>
    `

    const fragment = fragmentHTML.replace("{icon_path}", mod.icon_path)
        .replace("{name}", mod.name)
        .replace("{status}", mod.status);

    const modsList = document.getElementById("mods-list");
    modsList.innerHTML += fragment;
}

