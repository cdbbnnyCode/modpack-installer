const curseforge = require("mc-curseforge-api");
const fs = require("fs");
const path = require("path");
const async = require("async");
const http = require("https");

// Please note that my JS is *really* bad. Don't use this as an example of how
// to write javascript.

function download(url, dest, cb)
{
  var f = fs.createWriteStream(dest);
  var rq = http.get(url, {headers: {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}}, function(resp)
  {
    if (resp.statusCode != 200)
    {
      console.log("Non-200 status from " + url + ": " + resp.statusCode);
      fs.unlink(dest);
      if (cb) cb(resp.statusCode);
    }
    resp.pipe(f);
    f.on('finish', function()
    {
      f.close(cb);
    });
  }).on('error', function(err)
  {
    fs.unlink(dest);
    if (cb) cb(err.message);
  });
};

if (process.argv.length < 4)
{
  console.log("Usage: " + process.argv[0] + " " + process.argv[1] + " <json> <mod dir> <modlist json>");
  process.exit(0);
}
var pack_json = process.argv[2];
var mods_dir = process.argv[3];
var modlist_fname = process.argv[4];
/*
var packname = path.parse(pack_zip).name;
console.log('Extracting pack data ' + pack_zip);
fs.mkdir('.packs/' + packname, {}, (err) => {});
fs.createReadStream(pack_zip)
  .pipe(zip.Extract({path: '.packs/' + packname}))
  .on('close', function()
{
*/
console.log('Reading manifest file');
var manifest = JSON.parse(fs.readFileSync(pack_json));

var mods = manifest.files;
var mod_list = []
console.log('Got ' + mods.length + ' mods');
async.eachLimit(mods, 4, function(mod, callback)
{
  curseforge.getModFiles(mod.projectID).then(function(files)
  {
    var found = false;
    for (let f of files)
    {
      if (f.id == mod.fileID)
      {
        found = true;
        var outfile = path.resolve(mods_dir, f.file_name);
        mod_list.push(f.file_name);
        var ok = false;
        if (fs.existsSync(outfile))
        {
          var stats = fs.statSync(outfile);

          // Hack to approximate file size from KB/MB count
          // Might replace with md5 check in the future
          var fsize1 = parseFloat(f.file_size.slice(0, -3).replace(/,/g, ""));
          var fsize_ext = f.file_size.slice(-2);
          var fsize_mult = 1;
          if (fsize_ext == 'KB') fsize_mult = 1024;
          else if (fsize_ext == 'MB') fsize_mult = 1024 * 1024;
          var fsize = Math.floor(fsize1 * fsize_mult);
          if (stats.size >= 0.8 * fsize) ok = true;
        }

        if (!ok)
        {
          // This works and is apparently how the files are organized
          var id1 = Math.floor(f.id / 1000);
          var id2 = f.id % 1000;
          // This is because some people think it's OK to have weird characters
          // in their files. IT'S NOT OK!
          urlname = encodeURIComponent(f.file_name);

          url = `https://media.forgecdn.net/files/${id1}/${id2}/${urlname}`;
          console.log("Downloading " + url + " (" + f.mod_key + ")...");
          // Pound Curseforge's servers with hundreds of requests for mods
          // except we're legit bots not DoS'ing
          // Twitch client does this anyway so we can assume their servers don't
          // really care that much
          download(url, outfile, function(err)
          {
            if (err)
            {
              console.log(err);
              process.exit(1);
            }
          });

          // console.log("Manual download: " + f.download_url);
          callback();
        }
        else
        {
          console.log(f.file_name + " OK");
          callback();
        }
      }
    }
    if (!found)
    {
      console.log("---- " + mod.projectID + " not found");
      callback(); // Couldn't find file
    }
  });
}, function(err)
{
  if (err)
  {
    console.log(err);
    return;
  }

  var modlist_json = JSON.stringify({mods: mod_list});
  fs.writeFile(modlist_fname, modlist_json, function(err)
  {
    if (err) console.log(err);
  });
});
// });
