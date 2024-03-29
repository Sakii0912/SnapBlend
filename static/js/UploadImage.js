var image_list = [];
function dragOverHandler(event) {
    event.preventDefault();
}

function dropHandler(event) {
    event.preventDefault();
    const imgs = event.dataTransfer.files;
    handleFiles(imgs);
}
var length = 0;
var file_list_global;
const extensions=['image/jpeg' , 'image/jpg' , 'image/png'];
function handleFiles(IMG) {
    length = IMG.length;
    const fileList = document.getElementById('fileList');
    file_list_global = fileList;
    for (let i = 0; i < IMG.length; i++) {
        const img = IMG[i];
        if(extensions.includes(img.type))
        {
            image_list.push(img);
            const listItem = document.createElement('li');
            listItem.className = 'fileItem';
            listItem.textContent = img.name + '.';
            fileList.appendChild(listItem);
        }
        else;
    }
}
function deletefiles()
{
    image_list.splice(-1 , 1);
    console.log(image_list.length);
    if(file_list_global.lastChild)
    file_list_global.removeChild(file_list_global.lastChild);
    else
    alert("All images have been deleted!");
}
function submitimages(event){
    for(var i = 0 ; i<image_list.length ; i++)
    {
        console.log(image_list[i] + '\n');
    }
    event.preventDefault();
    const formdata = new FormData();
    image_list.forEach(function (file) {
        formdata.append('Images[]' , file);
    });
    formdata.append('user_id' , user_id);
    const xhr = new XMLHttpRequest();
    xhr.open('POST' , '/up_load');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                document.open();
                document.write(xhr.responseText);
                document.close();
            } 
            else;
        }
    };
    image_list = [];
    xhr.send(formdata);
}
