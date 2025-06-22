let get_data = async() => {
       
    let panelsData = await JSON.parse(data);

    var comicTitle = document.createElement('h1');
    comicTitle.className = 'comic-title'
    comicTitle.appendChild(document.createTextNode(panelsData.title));
    document.body.appendChild(comicTitle);


    var abstractContainer = document.createElement('div');
    abstractContainer.className = 'abstract-container'
    var abstractContainer_p = document.createElement('p');
    abstractContainer_p.appendChild(document.createTextNode(panelsData.abstract));
    abstractContainer.appendChild(abstractContainer_p)
    
    document.body.appendChild(abstractContainer);


    var gridContainer = document.createElement('div');
    gridContainer.className = 'grid-container'

    panelsData.panels.forEach(element => {
        var gridItem = document.createElement('div');
        gridItem.className = 'grid-item'
        var gridItem_img = document.createElement('img');
        gridItem_img['src'] =  element.img
        gridItem.appendChild(gridItem_img)
        gridContainer.appendChild(gridItem)
    });

    document.body.appendChild(gridContainer);

    // const printButton = document.createElement("button");
    // printButton.textContent = "Print this page";
    // printButton.addEventListener("click", function() {
    //     window.print();
    // });
    
    // document.body.appendChild(printButton);

  }

  get_data();