import path from "path"
import npyjs from 'npyjs'
import JSZip from 'jszip'
import fs from "fs"
const npz_file = '/home/n/document/code/GVHMR/output/demo/背越式跳高（慢动作）/preprocess/yolo_track.npz'
const dataPath = path.resolve(npz_file)
let contents = fs.readFileSync(npz_file)

const jsZip = new JSZip()
const npzFiles = await jsZip.loadAsync(contents)
const _npyjs_ = new npyjs()

let data = Object.entries(npzFiles.files)

for (const [npy_filename, npy_data] of Object.entries(npzFiles.files)) {
    if (!npy_filename.endsWith('.npy')) {
        console.error('error .npy')
    }

    const npy_array_buffer = await npzFiles.files[npy_filename].async("arraybuffer")
    console.log({ npy_filename, npy_data, npy_array_buffer: npy_array_buffer })

    data[npy_filename] = await _npyjs_.parse(npy_array_buffer)
}