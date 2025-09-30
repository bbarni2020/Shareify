import SwiftUI
import UIKit

struct ZoomableImageView: UIViewRepresentable {
    let image: UIImage
    
    func makeUIView(context: Context) -> UIScrollView {
        let scrollView = UIScrollView()
        let imageView = UIImageView(image: image)
        
        scrollView.delegate = context.coordinator
        scrollView.minimumZoomScale = 0.5
        scrollView.maximumZoomScale = 5.0
        scrollView.zoomScale = 1.0
        scrollView.showsVerticalScrollIndicator = true
        scrollView.showsHorizontalScrollIndicator = true
        scrollView.backgroundColor = .clear
        
        imageView.contentMode = .scaleAspectFit
        imageView.isUserInteractionEnabled = true
        
        scrollView.addSubview(imageView)
        
        imageView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            imageView.centerXAnchor.constraint(equalTo: scrollView.centerXAnchor),
            imageView.centerYAnchor.constraint(equalTo: scrollView.centerYAnchor),
            imageView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),
            imageView.heightAnchor.constraint(equalTo: scrollView.heightAnchor)
        ])
        
        let doubleTapGesture = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.doubleTapped(_:)))
        doubleTapGesture.numberOfTapsRequired = 2
        scrollView.addGestureRecognizer(doubleTapGesture)
        
        context.coordinator.scrollView = scrollView
        context.coordinator.imageView = imageView
        
        return scrollView
    }
    
    func updateUIView(_ uiView: UIScrollView, context: Context) {
        if let imageView = uiView.subviews.first as? UIImageView {
            imageView.image = image
        }
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator: NSObject, UIScrollViewDelegate {
        var scrollView: UIScrollView?
        var imageView: UIImageView?
        
        func viewForZooming(in scrollView: UIScrollView) -> UIView? {
            return imageView
        }
        
        func scrollViewDidZoom(_ scrollView: UIScrollView) {
            let offsetX = max((scrollView.bounds.width - scrollView.contentSize.width) * 0.5, 0)
            let offsetY = max((scrollView.bounds.height - scrollView.contentSize.height) * 0.5, 0)
            scrollView.contentInset = UIEdgeInsets(top: offsetY, left: offsetX, bottom: 0, right: 0)
        }
        
        @objc func doubleTapped(_ gesture: UITapGestureRecognizer) {
            guard let scrollView = scrollView else { return }
            
            if scrollView.zoomScale == scrollView.minimumZoomScale {
                let location = gesture.location(in: scrollView)
                let rect = CGRect(x: location.x - 50, y: location.y - 50, width: 100, height: 100)
                scrollView.zoom(to: rect, animated: true)
            } else {
                scrollView.setZoomScale(scrollView.minimumZoomScale, animated: true)
            }
        }
    }
}