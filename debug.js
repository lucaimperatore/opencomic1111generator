let get_data = async() => {
       
    let panelsData = await JSON.parse(data);

    var comicTitle = document.createElement('h1');
    comicTitle.className = 'comic-title'
    comicTitle.appendChild(document.createTextNode(panelsData.plot+ " - seed -> " + panelsData.seed) );
    document.body.appendChild(comicTitle);


    // var abstractContainer = document.createElement('div');
    // abstractContainer.className = 'abstract-container'
    // var abstractContainer_p = document.createElement('p');
    // abstractContainer_p.appendChild(document.createTextNode(panelsData.abstract));
    // abstractContainer.appendChild(abstractContainer_p)
    
    // var abstractContainer_plot = document.createElement('p');
    // abstractContainer_plot.appendChild(document.createTextNode(panelsData.plot));
    // abstractContainer.appendChild(abstractContainer_plot)
    
    // document.body.appendChild(abstractContainer);


    var gridContainer = document.createElement('div');
    gridContainer.className = 'grid-container-debug'

    panelsData.panels.forEach(element => {

        var gridItem = document.createElement('div');
        gridItem.className = 'grid-item-debug'

        var gridContainer_imgname = document.createElement('p');
        gridContainer_imgname.appendChild(document.createTextNode(element.img));
        gridItem.appendChild(gridContainer_imgname)

        
        var gridItem_img = document.createElement('img');
        gridItem_img['src'] =  element.img
        gridItem.appendChild(gridItem_img)

        var gridContainer_prompt = document.createElement('p');
        gridContainer_prompt.appendChild(document.createTextNode(element.prompt));
        gridItem.appendChild(gridContainer_prompt)

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