from pathlib import Path
import hashlib
import av


def probe_video(file_path):
    """
    Open video file with pyav and return some basic information about the video.
    
    Parameters
    ----------
    file_path : str or Path
        Path to the video file.
        
    Returns
    -------
    video_dict : dict
        Dictionary containing video information

    """
    file_path = Path(file_path)
    assert file_path.exists(), f"Video file {file_path} does not exist."
    file_path = file_path.as_posix()    
    container = av.open(file_path)
    # Find the first video stream.
    video_stream = next((s for s in container.streams if s.type == 'video'), None)
    if video_stream is None:
        raise ValueError(f"No video stream found in the file '{file_path}'")
    
    # Get video characteristics.
    codec = video_stream.codec_context.name
    width = video_stream.width
    height = video_stream.height
    fps = video_stream.average_rate
    num_frames = video_stream.frames
    # Calculate video duration in seconds.
    duration = float(num_frames / fps)

    print(f'File: {file_path}')
    print(f"Codec: {codec}")
    print(f"Resolution: {width} x {height}")
    print(f"Frame Rate: {fps}")
    print(f"Number of frames: {num_frames}")
    print(f"Duration: {duration:.2f} seconds")
    container.close()
    
    video_dict = {'codec': codec,
                  'height': height,
                  'width': width,
                  'fps': fps,
                  'num_frames': num_frames,
                  'duration': duration, # in seconds
                  }
    return video_dict


def get_vfile_hash(filepath, block_size=65536):
    """
    Get fast hash digest of video file using blake2b. 
    
    Parameters
    ----------
    filepath : str or Path
        Path to file.
    block_size : int
        Number of bytes to read at a time.
        
    Returns
    -------
    str : Hash digest.
    
    """
    filepath = Path(filepath)
    assert filepath.exists(), f'File does not exist: {filepath}'
    
    hasher = hashlib.blake2b(digest_size=32)
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()