if(Uid){
    if(img_dict){
        var SelectedImages = [];
        var container = document.getElementById('imageContainer');
        for(var i = 0 ; i<img_dict['Type'].length ; i++)
        {
            var Div = document.createElement("div");
            Div.classList.add("imageDiv");
            var blob = new Blob([new Uint8Array(img_dict['Data'][i])] , { type: 'image/' + img_dict['Type'][i]});
            var url  = URL.createObjectURL(blob);
            var button = document.createElement("button");
            button.className = "ImageButton";
            button.onclick = function(){
                this.classList.toggle("SelectedImage");
            }
            Div.appendChild(button);
            var imgele = document.createElement("img");
            imgele.src = url;
            imgele.alt = img_dict['Name'][i];
            button.appendChild(imgele);
            container.appendChild(Div);
        }
        var audioGallery = document.getElementById("AudioGallery");
// Iterate over the audio_files list
        for (var i = 0; i < audio_file['Data'].length; i++) {
    // Create a new audio element
    const audioDiv = document.createElement("div");
    audioDiv.classList.add("audio-div");

    var audioElement = document.createElement("audio");
         audioElement.controls = true;
    // Set the source of the audio element
        audioElement.src = "data:audio/mpeg;base64," + audio_file['Data'][i];

        const label = document.createElement("label");
        label.textContent = audio_file['Name'][i];
        label.classList.add("audio-label");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
    // Add the audio element to the AudioGallery section
        audioDiv.appendChild(label);
        audioDiv.appendChild(audioElement);
        audioDiv.appendChild(checkbox);

        audioGallery.appendChild(audioDiv);
        }


        function ImageAndAudioSelection(event){
        event.preventDefault();
        SelectedImages = [];
        SelectedAudios = [];
        var selects = document.querySelectorAll(".SelectedImage");
        var selecta = document.querySelectorAll(".audio-div");
        selects.forEach(function(image){
              SelectedImages.push(image.querySelector('img').alt);
        });
        selecta.forEach(function(audio){
            var check = audio.querySelector('input[type="checkbox"]');
            if(check.checked){
                SelectedAudios.push(audio.querySelector(".audio-label").textContent.trim());
            }
        });
        console.log(SelectedAudios);
        console.log(SelectedImages);
        const formdata = new FormData();
        SelectedImages.forEach(function(image_url){
            formdata.append('Image_URL[]' , image_url);
        });
        SelectedAudios.forEach(function(audio){
            formdata.append('Audionames[]' , audio);
        });
        formdata.append('userid', Uid);
        const xhr = new XMLHttpRequest();
        xhr.open('POST' , '/create_video');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    var data = JSON.parse(xhr.responseText)
                    var temp_data = atob(data.video_data)
                    var arrayBuffer = new ArrayBuffer(temp_data.length)
                    var bytearray = new Uint8Array(arrayBuffer)
                    for(var i = 0 ; i<temp_data.length ; i++)
                    {
                        bytearray[i] = temp_data.charCodeAt(i);
                    }
                    var blob = new Blob([bytearray] , { type: 'video/mp4' });
                    var url = URL.createObjectURL(blob);
                    var video_div = document.createElement("div");
                    var vid_sec = document.getElementById("video-preview");

                    var down_button = document.createElement("button");
                    
                    var vid = document.createElement("video");
                    vid.classList.add("video_style");
                    vid.src = url;
                    vid.controls = true;

                    var downloadlink = document.createElement("a"); 
                    downloadlink.href = url;
                    downloadlink.textContent = 'Download Video';
                    downloadlink.download = 'video.mp4';

                    down_button.appendChild(downloadlink);
                    video_div.appendChild(vid);
                    video_div.appendChild(down_button);

                    video_div.classList.add("video-container"); 
                    
                    vid_sec.appendChild(video_div);
                } 

            }
        };
        xhr.send(formdata);
   }
   function isValidMP4(data) {
    // Check if the data starts with the MP4 file signature bytes
    // MP4 files typically start with the "ftyp" box
    const strtindex = 8;
    const mp4Signature = [0x66, 0x74, 0x79, 0x70]; // ASCII values of 'ftyp'
    for (let i = 0; i < mp4Signature.length; i++) {
        if (data[i + strtindex] !== mp4Signature[i]) {
            return false;
        }
    }
    return true;
}
function binToHex(binaryData) {
    let hexString = '';
    for (let i = 0; i < binaryData.length; i++) {
        const hex = binaryData.charCodeAt(i).toString(16);
        hexString += (hex.length === 1 ? '0' : '') + hex; // Ensure two-digit hex representation
    }
    return hexString;
}
}
}